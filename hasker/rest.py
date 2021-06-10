from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View

from .models import Answer, AnswerVote, Question, QuestionVote


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
