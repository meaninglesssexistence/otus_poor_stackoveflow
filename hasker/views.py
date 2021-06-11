# -*- coding: utf-8 -*-
"""Обработчики запросов."""

from django import urls
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import F, Q, Count, Sum, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponseBadRequest, HttpResponseRedirect, Http404
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.html import escape, strip_tags
from django.views import View
from django.views.generic import ListView
from django.views.generic.edit import CreateView, FormView

from .models import Answer, Question, Tag
from .forms import AnswerForm, AskForm


def get_question_list_queryset():
    """Возвращает запрос списка вопросов с их авторами,
       подсчетом ответов и голосов.
    """

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


class QuestionListView(ListView):
    """Обработка запроса на вывод списка вопросов.

    Список выводится постранично. В зависимости от параметра
    запроса, меняется сортировка: по количеству голосов или
    по дате создания вопроса.
    """

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


class QuestionDetailView(ListView):
    """Обработка запроса на вывод вопроса и списка ответов.

    Список ответов выводится постранично с сортировкой по количеству
    голосов.
    """

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
    """Обработка запроса на создание нового ответа."""

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
    """Обработчик запросов, связанных в вопросом.

    При поступлении GET-запроса, обработка передается в QuestionDetailView для
    вывода параметров вопроса и списка ответов. При поступлении POST-запроса,
    обработка передается в QuestionAnswerView для создания нового ответа.
    """

    def get(self, request, question_id):
        view = QuestionDetailView.as_view()
        return view(request, question_id=question_id)

    def post(self, request, question_id):
        view = QuestionAnswerView.as_view()
        return view(request, question_id=question_id)


class AskFormView(LoginRequiredMixin, FormView):
    """Обработчик запроса на создание нового вопроса."""

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


class SearchListView(ListView):
    """Обработчик запроса на поиск по тексту.

    Поиск производится по тексту заголовка вопроса, тексту вопроса
    и ответов на вопрос. Если запрос имеет форму "tag: <тег>", из
    запроса извлекается имя тега и поиск ведется по тегам.
    """

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
