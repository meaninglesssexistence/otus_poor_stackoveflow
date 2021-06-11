# -*- coding: utf-8 -*-
"""Классы-модели для работы с вопросами, ответами и голосованием."""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Tag(models.Model):
    """Тег.

    Поля:
        text: текст тега
    """

    text = models.CharField(max_length=32, unique=True)

    def __str__(self):
        return self.text


class Question(models.Model):
    """Вопрос.

    Поля:
        title: заголовок вопроса
        text: описание вопроса
        creation_date: дата и время создания вопроса
        author: автор вопроса
        tags: список тегов вопроса (от 0 до 3)
        voters: пользователи, проголосовавшие за вопрос (за и против)
    """

    title = models.CharField(max_length=128)
    text = models.TextField(max_length=2048)
    creation_date = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag)
    voters = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='QuestionVote', related_name='questions')

    @property
    def tag_list(self):
        return self.tags.all()

    def __str__(self):
        return self.title


class Answer(models.Model):
    """Ответ на вопрос.

    Поля:
        text: текст ответа
        creation_date: дата и время создания вопроса
        correct: отметка верного ответа
        author: автор ответа
        question: вопрос, на который дан ответ
        voters: пользователи, проголосовавшие за ответ (за и против)
    """

    text = models.TextField(max_length=2048)
    creation_date = models.DateTimeField(default=timezone.now)
    correct = models.BooleanField(default=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    voters = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='AnswerVote', related_name='answers')

    def __str__(self):
        return self.text


class QuestionVote(models.Model):
    """Голос за вопрос.

    Поля:
        user: проголосовавший пользователь
        question: вопрос, за который отдан голос
        vote: значение голоса (за - 1, против - -1, воздержался - 0)

    Если пользователь не голосовал за вопрос, экземпляр QuestionVote
    не создается. Если он проголосовал за, а потом против, QuestionVote
    будет создан, но в поле vote будет сохранен 0.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE
    )
    vote = models.SmallIntegerField(
        default=0,
        validators=[
            MaxValueValidator(1),
            MinValueValidator(-1)
        ])

    class Meta:
        unique_together = ('user', 'question')


class AnswerVote(models.Model):
    """Голос за ответ.

    Поля:
        user: проголосовавший пользователь
        answer: ответ, за который отдан голос
        vote: значение голоса (за - 1, против - -1, воздержался - 0)

    Если пользователь не голосовал за ответ, экземпляр AnswerVote
    не создается. Если он проголосовал за, а потом против, AnswerVote
    будет создан, но в поле vote будет сохранен 0.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    answer = models.ForeignKey(
        Answer,
        on_delete=models.CASCADE
    )
    vote = models.SmallIntegerField(
        default=0,
        validators=[
            MaxValueValidator(1),
            MinValueValidator(-1)
        ])

    class Meta:
        unique_together = ('user', 'answer')
