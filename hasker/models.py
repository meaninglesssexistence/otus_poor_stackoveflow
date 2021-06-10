from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Tag(models.Model):
    text = models.CharField(max_length=32, unique=True)

    def __str__(self):
        return self.text


class Question(models.Model):
    title = models.CharField(max_length=128)
    text = models.TextField(max_length=2048)
    creation_date = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag)

    @property
    def tag_list(self):
        return self.tags.all()

    def __str__(self):
        return self.title


class Answer(models.Model):
    text = models.TextField(max_length=2048)
    creation_date = models.DateTimeField(default=timezone.now)
    correct = models.BooleanField(default=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    def __str__(self):
        return self.text


class QuestionVote(models.Model):
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
