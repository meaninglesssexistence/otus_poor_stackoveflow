import django.utils
import factory

from datetime import timedelta
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from factory.django import DjangoModelFactory

from hasker import models


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: 'User%d' % n)
    password = make_password('123')
    email = factory.LazyAttribute(lambda o: f'{o.username}@example.com')


class QuestionFactory(DjangoModelFactory):
    class Meta:
        model = models.Question

    _now = django.utils.timezone.now()

    id = factory.Sequence(lambda n: n + 1)
    title = factory.LazyAttribute(lambda o: f'Title {o.id-1}')
    text = factory.LazyAttribute(lambda o: f'Text {o.id-1}')
    creation_date = factory.Sequence(
        lambda n: QuestionFactory._now + timedelta(minutes=n)
    )
    author = factory.LazyAttribute(
        lambda o: User.objects.get(username=f'User{o.id-1}')
    )


class AnswerFactory(DjangoModelFactory):
    class Meta:
        model = models.Answer

    text = factory.Sequence(lambda n: 'Text %d' % n)
    correct = False
    author = factory.SubFactory(UserFactory)
    question = factory.SubFactory(QuestionFactory)


class QuestionVoteFactory(DjangoModelFactory):
    class Meta:
        model = models.QuestionVote

    user = factory.SubFactory(UserFactory)
    question = factory.SubFactory(QuestionFactory)
    vote = 1


class AnswerVoteFactory(DjangoModelFactory):
    class Meta:
        model = models.AnswerVote

    user = factory.SubFactory(UserFactory)
    answer = factory.SubFactory(AnswerFactory)
    vote = 1
 