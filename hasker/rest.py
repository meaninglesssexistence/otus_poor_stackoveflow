# -*- coding: utf-8 -*-
"""Обработчики REST-запросов на пометку правильного ответа и голосования.

Полноценный REST API для приложения не реализован, поэтому `rest_framework`
не применялся.
"""

from django.core.exceptions import PermissionDenied
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View

from .models import Answer, AnswerVote, Question, QuestionVote


class MarkSolutionView(View):
    """Обработка запроса на пометку верного ответа.

    Принимается POST-запрос. Если пользователь не аутентифицирован,
    выдается ошибка. Для всех ответов, кроме указанного, пометка
    снимается. Для указанного она снимается или устанавливается в
    зависимости от параметров запроса.

    Параметры:
        answer_id: идентификатор ответа
        is_set: True - пометка устанавливается, False - снимается.
    """

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

        return HttpResponse()


class QuestionVoteView(View):
    """Обработка запроса на голосование за вопрос.

    Принимается POST-запрос. Если пользователь не аутентифицирован,
    выдается ошибка. Если сумма голосов, отданных пользователем,
    выйдет за границы [-1, 1], выдается ошибка. Создается, при
    необходимости, новый экземпляр QuestionVote. В него записывается
    или обновляется голос.

    Параметры:
        question_id: идентификатор вопроса
        is_up: True - голос за, False - голос против.
    """
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
    """Обработка запроса на голосование за ответ.

    Принимается POST-запрос. Если пользователь не аутентифицирован,
    выдается ошибка. Если сумма голосов, отданных пользователем,
    выйдет за границы [-1, 1], выдается ошибка. Создается, при
    необходимости, новый экземпляр AnswerVote. В него записывается
    или обновляется голос.

    Параметры:
        answer_id: идентификатор ответа
        is_up: True - голос за, False - голос против.
    """

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
