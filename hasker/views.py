from django import urls
from django.conf import settings
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import F, Q, Count, Sum, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponseBadRequest, HttpResponseRedirect, JsonResponse, Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.template.loader import render_to_string
from django.utils.html import escape, strip_tags
from django.views import View
from django.views.generic import ListView
from django.views.generic.edit import CreateView, FormView

from .models import Answer, AnswerVote, Question, QuestionVote, Tag
from .forms import AnswerForm, AskForm, LoginForm, SignUpForm, SettingsForm


def get_question_list_queryset():
    return Question.objects.select_related(
        'author'
    ).prefetch_related(
        'tags'
    ).annotate(
        answers_count=Count('answer', distinct=True)
    ).annotate(
        votes_sum=Coalesce(
            Sum('questionvote__vote') * \
                Count('questionvote__id', distinct=True) / \
                Count('questionvote__id', distinct=False),
            Value(0)
        )
    )


class TrendingListViewMixin:
    trending_list = Question.objects.annotate(
        votes_sum=Coalesce(Sum('questionvote__vote'), Value(0))
    ).order_by(
        '-votes_sum', '-creation_date'
    ).all()[:settings.HASKER_TRENDING_SIZE]


class QuestionListView(ListView, TrendingListViewMixin):
    paginate_by = settings.HASKER_QUESTION_LIST_PAGE
    template_name = 'hasker/index.html'
    queryset = get_question_list_queryset()

    def get_ordering(self):
        if self.is_hot():
            return ['-votes_sum', '-creation_date']
        else:
            return ['-creation_date', '-votes_sum']

    def is_hot(self):
        return self.request.GET.get('sort', '') == 'hot'


class QuestionDetailView(ListView, TrendingListViewMixin):
    paginate_by = settings.HASKER_ANSWER_LIST_PAGE
    template_name = 'hasker/question.html'

    def get_queryset(self):
        return Answer.objects.filter(
            question__id=self.kwargs['question_id']
        ).select_related(
            'author', 'author__useravatar'
        ).annotate(
            votes_sum=Coalesce(Sum('answervote__vote'), Value(0))
        ).order_by(
            '-votes_sum'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = AnswerForm()

        questions = Question.objects.filter(
            id=self.kwargs['question_id']
        ).select_related(
            'author'
        ).prefetch_related(
            'tags'
        ).annotate(
            votes_sum=Coalesce(Sum('questionvote__vote'), Value(0))
        )

        if not questions:
            raise Http404

        context['question'] = questions[0]

        return context


class QuestionAnswerView(LoginRequiredMixin, CreateView):
    form_class = AnswerForm
    model = Answer

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.author = self.request.user
        self.object.question_id=self.kwargs['question_id']
        self.object.save()

        # Send e-mail to the question's author if
        # he/she has an e-mail address.
        if self.object.question.author.email:
            self.send_email()

        return super().form_valid(form)

        return HttpResponseRedirect(self.get_success_url())

    def send_email(self):
        answer = self.object
        html_message = render_to_string(
            'hasker/mail-answer.html',
            {
                'question_url': self.request.build_absolute_uri(
                    urls.reverse(
                        'question', args=[answer.question.id])
                    ),
                'question_text': answer.question.text,
                'answer_user': answer.author.username,
                'answer_text': answer.text
            }
        )

        send_mail(
            subject='Your question has an answer!',
            message=strip_tags(html_message),
            html_message=html_message,
            from_email=settings.HASKER_SEND_MAIL_FROM,
            recipient_list=[answer.question.author.email]
        )

    def get_success_url(self):
        return urls.reverse(
            'question', kwargs={'question_id': self.kwargs['question_id']}
        )


class QuestionView(View):

    def get(self, request, question_id):
        view = QuestionDetailView.as_view()
        return view(request, question_id=question_id)

    def post(self, request, question_id):
        view = QuestionAnswerView.as_view()
        return view(request, question_id=question_id)


class AskFormView(LoginRequiredMixin, FormView, TrendingListViewMixin):
    template_name = 'hasker/ask.html'
    form_class = AskForm
    all_tags = Tag.objects.order_by('text')

    def form_valid(self, form):
        self.question = form.save(commit=False)
        self.question.author = self.request.user
        self.question.save()

        for tag_text in form.cleaned_data.get('tags'):
            tag, _ = Tag.objects.get_or_create(text=tag_text)
            self.question.tags.add(tag)

        return super().form_valid(form)

    def get_success_url(self):
        return urls.reverse(
            'question', kwargs={'question_id': self.question.id}
        )


class MarkSolutionView(View):

    def post(self, request, answer_id, is_set):
        solution = Answer.objects.get(pk=answer_id)
        question = Question.objects.get(pk=solution.question.id)

        if not request.user.is_authenticated or \
           question.author != request.user:
            raise PermissionDenied

        answers = Answer.objects.filter(question=question).all()
        for answer in answers:
            answer.correct = is_set if answer == solution else False
        Answer.objects.bulk_update(answers, ['correct'])

        return JsonResponse({})


class QuestionVoteView(View):

    def post(self, request, question_id, is_up):
        if not request.user.is_authenticated:
            raise PermissionDenied

        question = get_object_or_404(Question, pk=question_id)

        old_vote, _ = QuestionVote.objects.get_or_create(
            user_id=self.request.user.id,
            question_id=question_id)

        vote = 1 if is_up else -1

        if not (old_vote.vote + vote) in (-1, 0, 1):
            return HttpResponseBadRequest()

        old_vote.vote = old_vote.vote + vote
        old_vote.save()

        question = Question.objects.filter(
            id=question_id
        ).annotate(
            votes_sum=Coalesce(Sum('questionvote__vote'), Value(0))
        )

        return JsonResponse({'votes': question[0].votes_sum})


class AnswerVoteView(View):

    def post(self, request, answer_id, is_up):
        if not request.user.is_authenticated:
            raise PermissionDenied

        question = get_object_or_404(Answer, pk=answer_id)

        old_vote, _ = AnswerVote.objects.get_or_create(
            user_id=self.request.user.id,
            answer_id=answer_id)

        vote = 1 if is_up else -1

        if not (old_vote.vote + vote) in (-1, 0, 1):
            return HttpResponseBadRequest()

        old_vote.vote = old_vote.vote + vote
        old_vote.save()

        answers = Answer.objects.filter(
            id=answer_id
        ).annotate(
            votes_sum=Coalesce(Sum('answervote__vote'), Value(0))
        )

        return JsonResponse({'votes': answers[0].votes_sum})


class LoginFormView(LoginView, TrendingListViewMixin):
    template_name = 'login.html'
    form_class = LoginForm


class SignupFormView(FormView, TrendingListViewMixin):
    template_name = 'signup.html'
    form_class = SignUpForm
    success_url = urls.reverse_lazy('index')

    def form_valid(self, form):
        # Create new user
        user = form.save()
        user.refresh_from_db()
        user.useravatar.avatar = form.cleaned_data.get('avatar')
        user.save()
        password = form.cleaned_data.get('password1')
        # Login new user
        user = authenticate(username=user.username, password=password)
        login(self.request, user)
        return super().form_valid(form)


class SettingsFormView(LoginRequiredMixin, FormView, TrendingListViewMixin):
    template_name = 'hasker/settings.html'
    form_class = SettingsForm
    success_url = urls.reverse_lazy('index')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.useravatar.avatar = form.cleaned_data.get('avatar')
        user.save()
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.request.user
        kwargs['initial'] = {'avatar': self.request.user.useravatar.avatar}
        return kwargs


class SearchListView(ListView, TrendingListViewMixin):
    paginate_by = settings.HASKER_QUESTION_LIST_PAGE

    def get(self, request, tag=None):
        self.tag = tag
        self.search_text = request.GET.get('q', '').strip()

        if self.search_text.startswith('tag:'):
            return redirect(
                'search_tag',
                tag=escape(self.search_text[4:].strip())
            )
        return super().get(request)

    def get_queryset(self):
        if self.tag:
            query = Q(tags__text=self.tag)
        else:
            query = Q(title__contains=f'{self.search_text}')
            query.add(Q(text__contains=f'{self.search_text}'), Q.OR)

        return get_question_list_queryset().filter(query).order_by(
            '-votes_sum', '-creation_date'
        )
