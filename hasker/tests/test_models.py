from datetime import datetime
from django.contrib.auth.models import User
from django.test import TestCase

from hasker import models


class AnswerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('john', 'john@example.com', '123')
        self.question = models.Question.objects.create(
            title='To be or not to be',
            text='that is the questionm',
            author=self.user
        )
        self.answer = models.Answer.objects.create(
            text='Answer',
            author=self.user,
            question=self.question
        )

    def test_default_value(self):
        self.assertFalse(self.answer.correct)
        self.assertEqual(
            datetime.now().date(),
            self.answer.creation_date.date()
        )

    def test_removing_on_question_removing(self):
        self.question.delete()

        answers = models.Answer.objects.all()
        self.assertEqual(0, len(answers))


class AnswerVoteTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('john', 'john@example.com', '123')
        self.question = models.Question.objects.create(
            title='To be or not to be',
            text='that is the questionm',
            author=self.user
        )
        self.answer = models.Answer.objects.create(
            text='Answer',
            author=self.user,
            question=self.question
        )
        self.vote = models.AnswerVote.objects.create(
            user=self.user,
            answer=self.answer
        )

    def test_removing_on_answer_removing(self):
        self.answer.delete()

        votes = models.AnswerVote.objects.all()
        self.assertEqual(0, len(votes))

    def test_removing_on_user_removing(self):
        self.user.delete()

        votes = models.AnswerVote.objects.all()
        self.assertEqual(0, len(votes))

    def test_default_value(self):
        self.assertEqual(0, self.vote.vote)


class QuestionTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('john', 'john@example.com', '123')
        self.tag1 = models.Tag.objects.create(text='Tag1')
        self.tag2 = models.Tag.objects.create(text='Tag2')

    def test_removing_on_user_removing(self):
        question = models.Question.objects.create(
            title='To be or not to be',
            text='that is the questionm',
            author=self.user
        )

        self.user.delete()

        questions = models.Question.objects.all()
        self.assertEqual(0, len(questions))

    def test_null_on_tag_removing(self):
        question = models.Question.objects.create(
            title='To be or not to be',
            text='that is the questionm',
            author=self.user,
            tag1=self.tag1
        )

        self.tag1.delete()

        questions = models.Question.objects.all()
        self.assertEqual(1, len(questions))
        self.assertIsNone(questions[0].tag1)

    def test_tags_property(self):
        question = models.Question.objects.create(
            title='To be or not to be',
            text='that is the questionm',
            author=self.user,
            tag1=self.tag1, tag2=self.tag2
        )

        self.assertEqual([self.tag1, self.tag2], question.tags)

    def test_default_value(self):
        question = models.Question.objects.create(
            title='To be or not to be',
            text='that is the questionm',
            author=self.user
        )

        self.assertEqual(datetime.now().date(), question.creation_date.date())        


class QuestionVoteTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('john', 'john@example.com', '123')
        self.question = models.Question.objects.create(
            title='To be or not to be',
            text='that is the questionm',
            author=self.user
        )
        self.vote = models.QuestionVote.objects.create(
            user=self.user,
            question=self.question
        )

    def test_removing_on_question_removing(self):
        self.question.delete()

        votes = models.QuestionVote.objects.all()
        self.assertEqual(0, len(votes))

    def test_removing_on_user_removing(self):
        self.user.delete()

        votes = models.QuestionVote.objects.all()
        self.assertEqual(0, len(votes))

    def test_default_value(self):
        self.assertEqual(0, self.vote.vote)


class UserAvatarTest(TestCase):
    def test_avatar_creation_on_user_creation(self):
        user = User.objects.create_user('john', 'john@example.com', '123')
        avatars = models.UserAvatar.objects.all()

        self.assertEqual(1, len(avatars))
        self.assertFalse(avatars[0].avatar)

    def test_avatar_removing_on_user_removing(self):
        user = User.objects.create_user('john', 'john@example.com', '123')

        avatars = models.UserAvatar.objects.all()
        self.assertEqual(1, len(avatars))

        user.delete()

        avatars = models.UserAvatar.objects.all()
        self.assertEqual(0, len(avatars))
