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
from django.http import HttpResponseBadRequest, JsonResponse, Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.template.loader import render_to_string
from django.utils.html import escape, strip_tags
from django.views import View
from django.views.generic import ListView
from django.views.generic.edit import FormView

from . import models
from . import forms


def get_question_list_queryset():
    return models.Question.objects.select_related(
        'author', 'tag1', 'tag2', 'tag3'
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
    trending_list = models.Question.objects.annotate(
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
        return models.Answer.objects.filter(
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
        context['form'] = forms.AnswerForm()

        questions = models.Question.objects.filter(
            id=self.kwargs['question_id']
        ).select_related(
            'author', 'tag1', 'tag2', 'tag3'
        ).annotate(
            votes_sum=Coalesce(Sum('questionvote__vote'), Value(0))
        )

        if not questions:
            raise Http404

        context['question'] = questions[0]

        return context


class QuestionAnswerView(LoginRequiredMixin, FormView):
    form_class = forms.AnswerForm

    def form_valid(self, form):
        a = models.Answer(
            text=form.cleaned_data['text'],
            author=self.request.user,
            question_id=self.kwargs['question_id'])
        a.save()

        # Send e-mail to the question's author.
        if a.question.author.email:
            self.send_email(a, a.question.author.email)

        return super().form_valid(form)

    def send_email(self, answer, email):
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
            recipient_list=[email]
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
    form_class = forms.AskForm
    all_tags = models.Tag.objects.order_by('text')

    def form_valid(self, form):
        self.question = form.save(commit=False)
        self.question.author = self.request.user

        tag_texts = form.cleaned_data.get('tags')
        if len(tag_texts) > 0:
            self.question.tag1 = models.Tag.objects.get_or_create(
                text=tag_texts[0])[0]
        if len(tag_texts) > 1:
            self.question.tag2 = models.Tag.objects.get_or_create(
                text=tag_texts[1])[0]
        if len(tag_texts) > 2:
            self.question.tag3 = models.Tag.objects.get_or_create(
                text=tag_texts[2])[0]

        self.question.save()
        return super().form_valid(form)

    def get_success_url(self):
        return urls.reverse(
            'question', kwargs={'question_id': self.question.id}
        )


class MarkSolutionView(View):

    def post(self, request, answer_id, is_set):
        solution = models.Answer.objects.get(pk=answer_id)
        question = models.Question.objects.get(pk=solution.question.id)

        if not request.user.is_authenticated or \
           question.author != request.user:
            raise PermissionDenied

        answers = models.Answer.objects.filter(question=question).all()
        for answer in answers:
            answer.correct = is_set if answer == solution else False
        models.Answer.objects.bulk_update(answers, ['correct'])

        return JsonResponse({})


class QuestionVoteView(View):

    def post(self, request, question_id, is_up):
        if not request.user.is_authenticated:
            raise PermissionDenied

        question = get_object_or_404(models.Question, pk=question_id)

        old_vote, _ = models.QuestionVote.objects.get_or_create(
            user_id=self.request.user.id,
            question_id=question_id)

        vote = 1 if is_up else -1

        if not (old_vote.vote + vote) in (-1, 0, 1):
            return HttpResponseBadRequest()

        old_vote.vote = old_vote.vote + vote
        old_vote.save()

        question = models.Question.objects.filter(
            id=question_id
        ).annotate(
            votes_sum=Coalesce(Sum('questionvote__vote'), Value(0))
        )

        return JsonResponse({'votes': question[0].votes_sum})


class AnswerVoteView(View):

    def post(self, request, answer_id, is_up):
        if not request.user.is_authenticated:
            raise PermissionDenied

        question = get_object_or_404(models.Answer, pk=answer_id)

        old_vote, _ = models.AnswerVote.objects.get_or_create(
            user_id=self.request.user.id,
            answer_id=answer_id)

        vote = 1 if is_up else -1

        if not (old_vote.vote + vote) in (-1, 0, 1):
            return HttpResponseBadRequest()

        old_vote.vote = old_vote.vote + vote
        old_vote.save()

        answers = models.Answer.objects.filter(
            id=answer_id
        ).annotate(
            votes_sum=Coalesce(Sum('answervote__vote'), Value(0))
        )

        return JsonResponse({'votes': answers[0].votes_sum})


class LoginFormView(LoginView, TrendingListViewMixin):
    template_name = 'login.html'
    form_class = forms.LoginForm


class SignupFormView(FormView, TrendingListViewMixin):
    template_name = 'signup.html'
    form_class = forms.SignUpForm
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
    form_class = forms.SettingsForm
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
            query = Q(tag1__text=self.tag)
            query.add(Q(tag2__text=self.tag), Q.OR)
            query.add(Q(tag3__text=self.tag), Q.OR)
        else:
            query = Q(title__contains=f'{self.search_text}')
            query.add(Q(text__contains=f'{self.search_text}'), Q.OR)

        return get_question_list_queryset().filter(query).order_by(
            '-votes_sum', '-creation_date'
        )
