import django.utils
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.core import mail
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
from django.test import TestCase
from django.urls import reverse

from hasker import models, views

def createTestData(question_num):
    user_num = 30
    answer_num = max(30, question_num)
    question_vote_num = max(30, question_num)
    answer_vote_num = max(30, answer_num)

    for user_id in range(user_num):
        User.objects.create_user(
            f'User{user_id}', f'{user_id}@example.com', '123'
        )

    now = django.utils.timezone.now()
    for question_id in range(question_num):
        now = now + timedelta(minutes=1)
        question = models.Question.objects.create(
            title=f'Title {question_id}',
            text=f'Text {question_id}',
            creation_date=now,
            author=User.objects.get(username=f'User{question_id}')
        )
        if question_id != 0:
            for vote_id in range(question_vote_num - question_id):
                models.QuestionVote.objects.create(
                    user=User.objects.get(username=f'User{vote_id}'),
                    question=question,
                    vote=1
                )
        if question_id != (question_num - 1):
            for answer_id in range(answer_num - question_id):
                answer = models.Answer.objects.create(
                    text=f'Text {answer_id}',
                    author=User.objects.get(username=f'User{answer_id}'),
                    question=question
                )
                if answer_id != 0:
                    for vote_id in range(answer_vote_num - answer_id):
                        models.AnswerVote.objects.create(
                            user=User.objects.get(username=f'User{vote_id}'),
                            answer=answer,
                            vote=1
                        )


class QuestionListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        createTestData(question_num=30)

    def test_default_url(self):
        response = self.client.get('/hasker/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('is_paginated' in response.context)
        self.assertTrue(response.context['is_paginated'] == True)
        self.assertEqual(20, len(response.context['question_list']))
        self.assertEqual(1, response.context['question_list'][0].votes_sum)
        self.assertEqual(0, response.context['question_list'][0].answers_count)
        self.assertEqual(20, response.context['question_list'][19].votes_sum)
        self.assertEqual(
            20, response.context['question_list'][19].answers_count
        )

    def test_default_second_page(self):
        response = self.client.get(reverse('index')+'?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('is_paginated' in response.context)
        self.assertTrue(response.context['is_paginated'] == True)
        self.assertEqual(10, len(response.context['question_list']))
        self.assertEqual(21, response.context['question_list'][0].votes_sum)
        self.assertEqual(21, response.context['question_list'][0].answers_count)
        self.assertEqual(0, response.context['question_list'][9].votes_sum)
        self.assertEqual(30, response.context['question_list'][9].answers_count)

    def test_hot_url(self):
        response = self.client.get('/hasker/?sort=hot')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('is_paginated' in response.context)
        self.assertTrue(response.context['is_paginated'] == True)
        self.assertEqual(20, len(response.context['question_list']))
        self.assertEqual(29, response.context['question_list'][0].votes_sum)
        self.assertEqual(29, response.context['question_list'][0].answers_count)
        self.assertEqual(10, response.context['question_list'][19].votes_sum)
        self.assertEqual(10, response.context['question_list'][19].answers_count)

    def test_hot_second_page(self):
        response = self.client.get(reverse('index')+'?page=2&sort=hot')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('is_paginated' in response.context)
        self.assertTrue(response.context['is_paginated'] == True)
        self.assertEqual(10, len(response.context['question_list']))
        self.assertEqual(9, response.context['question_list'][0].votes_sum)
        self.assertEqual(9, response.context['question_list'][0].answers_count)
        self.assertEqual(0, response.context['question_list'][9].votes_sum)
        self.assertEqual(30, response.context['question_list'][9].answers_count)


class QuestionViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        createTestData(question_num=3)

    def test_invalid_question(self):
        response = self.client.get('/hasker/question/999/')
        self.assertEqual(404, response.status_code)

    def test_first_page_answers(self):
        question = models.Question.objects.filter(title='Title 1').first()

        response = self.client.get(f'/hasker/question/{question.id}/')
        self.assertEqual(200, response.status_code)
        self.assertTrue('is_paginated' in response.context)
        self.assertTrue(response.context['is_paginated'] == True)
        self.assertEqual(25, len(response.context['answer_list']))
        self.assertEqual(29, response.context['answer_list'][0].votes_sum)
        self.assertEqual(5, response.context['answer_list'][24].votes_sum)

    def test_second_page_answers(self):
        question = models.Question.objects.filter(title='Title 1').first()

        response = self.client.get(
            reverse('question', kwargs={'question_id': question.id})+'?page=2'
        )
        self.assertEqual(200, response.status_code)
        self.assertTrue('is_paginated' in response.context)
        self.assertTrue(response.context['is_paginated'] == True)
        self.assertEqual(4, len(response.context['answer_list']))
        self.assertEqual(4, response.context['answer_list'][0].votes_sum)
        self.assertEqual(0, response.context['answer_list'][3].votes_sum)

    def test_new_answer_saving(self):
        question = models.Question.objects.filter(title='Title 1').first()

        self.client.login(username='User0', password='123')
        response = self.client.post(
            reverse('question', kwargs={'question_id': question.id}),
            {'text': 'Answer text.'}
        )
        self.assertRedirects(
            response,
            reverse('question', kwargs={'question_id': question.id})
        )
        self.assertEqual(
            30,
            models.Answer.objects.filter(question__id=question.id).count()
        )
        self.assertEqual(1, len(mail.outbox))

    def test_new_answer_requires_login(self):
        question = models.Question.objects.filter(title='Title 1').first()
        answer_count = models.Answer.objects.filter(
            question__id=question.id
        ).count()

        response = self.client.post(
            reverse('question', kwargs={'question_id': question.id}),
            {'text': 'Answer text.'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            f'/hasker/login?next=/hasker/question/{question.id}/',
            response.url
        )
        self.assertEqual(
            answer_count,
            models.Answer.objects.filter(question__id=question.id).count()
        )
        self.assertEqual(0, len(mail.outbox))


class AskFormViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        createTestData(question_num=1)

    def test_new_question(self):
        self.client.login(username='User0', password='123')
        response = self.client.post(
            reverse('ask'), {'title': 'TitleX', 'text': 'Question text.'}
        )

        question = models.Question.objects.filter(title='TitleX').first()
        self.assertEqual('Question text.', question.text)
        self.assertEqual('User0', question.author.username)

        self.assertRedirects(
            response,
            reverse('question', kwargs={'question_id': question.id})
        )

    def test_tag_creation(self):
        self.client.login(username='User0', password='123')
        response = self.client.post(
            reverse('ask'),
            {'title': 'TitleY', 'text': 'Question text.', 'tags': 'tag1, tag2'}
        )

        question = models.Question.objects.filter(title='TitleY').first()
        self.assertEqual(2, models.Tag.objects.count())
        self.assertTrue(models.Tag.objects.get(text='tag1') in question.tag_list)
        self.assertTrue(models.Tag.objects.get(text='tag2') in question.tag_list)
        self.assertRedirects(
            response,
            reverse('question', kwargs={'question_id': question.id})
        )

    def test_asking_requires_login(self):
        total_questions = models.Question.objects.count()
        response = self.client.post(
            reverse('ask'), {'title': 'Title', 'text': 'Question text.'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual('/hasker/login?next=/hasker/question/ask/', response.url)
        self.assertEqual(total_questions, models.Question.objects.count())


class MarkSolutionViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        createTestData(question_num=3)

    def test_set_clear_solution(self):
        question = models.Question.objects.filter(title='Title 1').first()
        answers = models.Answer.objects.filter(question__id=question.id)

        self.client.login(username=question.author.username, password='123')

        response = self.client.post(
            reverse('solution-set', kwargs={'answer_id': answers[0].id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(models.Answer.objects.get(pk=answers[0].id).correct)
        self.assertFalse(models.Answer.objects.get(pk=answers[1].id).correct)

        response = self.client.post(
            reverse('solution-clear', kwargs={'answer_id': answers[0].id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(models.Answer.objects.get(pk=answers[0].id).correct)
        self.assertFalse(models.Answer.objects.get(pk=answers[1].id).correct)

    def test_change_solution(self):
        question = models.Question.objects.filter(title='Title 1').first()
        answers = models.Answer.objects.filter(question__id=question.id)

        self.client.login(username=question.author.username, password='123')

        response = self.client.post(
            reverse('solution-set', kwargs={'answer_id': answers[0].id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(models.Answer.objects.get(pk=answers[0].id).correct)
        self.assertFalse(models.Answer.objects.get(pk=answers[1].id).correct)

        response = self.client.post(
            reverse('solution-set', kwargs={'answer_id': answers[1].id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(models.Answer.objects.get(pk=answers[0].id).correct)
        self.assertTrue(models.Answer.objects.get(pk=answers[1].id).correct)

    def test_solution_set_requires_question_author(self):
        question = models.Question.objects.filter(title='Title 1').first()
        answer = models.Answer.objects.filter(question__id=question.id).first()

        response = self.client.post(
            reverse('solution-set', kwargs={'answer_id': answer.id})
        )
        self.assertEqual(response.status_code, 403)

        self.client.login(username='User0', password='123')
        response = self.client.post(
            reverse('solution-set', kwargs={'answer_id': answer.id})
        )
        self.assertEqual(response.status_code, 403)

    def test_solution_clear_requires_question_author(self):
        question = models.Question.objects.filter(title='Title 1').first()
        answer = models.Answer.objects.filter(question__id=question.id).first()

        response = self.client.post(
            reverse('solution-clear', kwargs={'answer_id': answer.id})
        )
        self.assertEqual(response.status_code, 403)

        self.client.login(username='User0', password='123')
        response = self.client.post(
            reverse('solution-clear', kwargs={'answer_id': answer.id})
        )
        self.assertEqual(response.status_code, 403)


class QuestionVoteViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        createTestData(question_num=3)

    @staticmethod
    def _get_votes_sum(question):
        return models.QuestionVote.objects.filter(
            question__id=question.id
        ).aggregate(
            votes_sum=Coalesce(Sum('vote'), Value(0))
        )['votes_sum']

    def setUp(self):
        User.objects.create_user(
            f'UserA', f'user_a@example.com', '123'
        )
        User.objects.create_user(
            f'UserB', f'user_b@example.com', '123'
        )

    def test_vote_min_max(self):
        self.client.login(username='UserA', password='123')

        question = models.Question.objects.filter(title='Title 1').first()

        init_votes = QuestionVoteViewTest._get_votes_sum(question)

        response = self.client.post(
            reverse('question-vote-up', kwargs={'question_id': question.id})
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(init_votes + 1, response.json()['votes'])
        self.assertEqual(
            init_votes + 1,
            QuestionVoteViewTest._get_votes_sum(question)
        )

        response = self.client.post(
            reverse('question-vote-up', kwargs={'question_id': question.id})
        )
        self.assertEqual(400, response.status_code)
        self.assertEqual(
            init_votes + 1,
            QuestionVoteViewTest._get_votes_sum(question)
        )

        response = self.client.post(
            reverse('question-vote-down', kwargs={'question_id': question.id})
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(init_votes + 0, response.json()['votes'])
        self.assertEqual(
            init_votes + 0,
            QuestionVoteViewTest._get_votes_sum(question)
        )

        response = self.client.post(
            reverse('question-vote-down', kwargs={'question_id': question.id})
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(init_votes - 1, response.json()['votes'])
        self.assertEqual(
            init_votes - 1,
            QuestionVoteViewTest._get_votes_sum(question)
        )

        response = self.client.post(
            reverse('question-vote-down', kwargs={'question_id': question.id})
        )
        self.assertEqual(400, response.status_code)
        self.assertEqual(
            init_votes - 1,
            QuestionVoteViewTest._get_votes_sum(question)
        )

    def test_vote_by_two_users(self):
        question = models.Question.objects.filter(title='Title 1').first()

        init_votes = QuestionVoteViewTest._get_votes_sum(question)

        self.client.login(username='UserA', password='123')
        response = self.client.post(
            reverse('question-vote-up', kwargs={'question_id': question.id})
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(init_votes + 1, response.json()['votes'])
        self.assertEqual(
            init_votes + 1, QuestionVoteViewTest._get_votes_sum(question)
        )

        self.client.login(username='UserB', password='123')
        response = self.client.post(
            reverse('question-vote-up', kwargs={'question_id': question.id})
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(init_votes + 2, response.json()['votes'])
        self.assertEqual(
            init_votes + 2,
            QuestionVoteViewTest._get_votes_sum(question)
        )

        response = self.client.post(
            reverse('question-vote-down', kwargs={'question_id': question.id})
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(init_votes + 1, response.json()['votes'])
        self.assertEqual(
            init_votes + 1,
            QuestionVoteViewTest._get_votes_sum(question)
        )

    def test_vote_requires_login(self):
        question = models.Question.objects.filter(title='Title 1').first()

        response = self.client.post(
            reverse('question-vote-up', kwargs={'question_id': question.id})
        )
        self.assertEqual(403, response.status_code, 403)

        response = self.client.post(
            reverse('question-vote-down', kwargs={'question_id': question.id})
        )
        self.assertEqual(403, response.status_code, 403)


class AnswerVoteViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        createTestData(question_num=3)

    @staticmethod
    def _get_votes_sum(answer):
        return models.AnswerVote.objects.filter(
            answer__id=answer.id
        ).aggregate(
            votes_sum=Coalesce(Sum('vote'), Value(0))
        )['votes_sum']

    def setUp(self):
        User.objects.create_user(
            f'UserA', f'user_a@example.com', '123'
        )
        User.objects.create_user(
            f'UserB', f'user_b@example.com', '123'
        )

    def test_vote_min_max(self):
        self.client.login(username='UserA', password='123')

        question = models.Question.objects.filter(title='Title 1').first()
        answer = models.Answer.objects.filter(question__id=question.id).first()

        init_votes = AnswerVoteViewTest._get_votes_sum(answer)

        response = self.client.post(
            reverse('answer-vote-up', kwargs={'answer_id': answer.id})
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(init_votes + 1, response.json()['votes'])
        self.assertEqual(
            init_votes + 1,
            AnswerVoteViewTest._get_votes_sum(answer)
        )

        response = self.client.post(
           reverse('answer-vote-up', kwargs={'answer_id': answer.id})
        )
        self.assertEqual(400, response.status_code)
        self.assertEqual(
            init_votes + 1,
            AnswerVoteViewTest._get_votes_sum(answer)
        )

        response = self.client.post(
           reverse('answer-vote-down', kwargs={'answer_id': answer.id})
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(init_votes + 0, response.json()['votes'])
        self.assertEqual(
            init_votes + 0,
            AnswerVoteViewTest._get_votes_sum(answer)
        )

        response = self.client.post(
           reverse('answer-vote-down', kwargs={'answer_id': answer.id})
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(init_votes - 1, response.json()['votes'])
        self.assertEqual(
            init_votes - 1,
            AnswerVoteViewTest._get_votes_sum(answer)
        )

        response = self.client.post(
           reverse('answer-vote-down', kwargs={'answer_id': answer.id})
        )
        self.assertEqual(400, response.status_code)
        self.assertEqual(
            init_votes - 1,
            AnswerVoteViewTest._get_votes_sum(answer)
        )

    def test_vote_by_two_users(self):
        question = models.Question.objects.filter(title='Title 1').first()
        answer = models.Answer.objects.filter(question__id=question.id).first()

        init_votes = AnswerVoteViewTest._get_votes_sum(answer)

        self.client.login(username='UserA', password='123')
        response = self.client.post(
            reverse('answer-vote-up', kwargs={'answer_id': answer.id})
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(init_votes + 1, response.json()['votes'])
        self.assertEqual(
            init_votes + 1,
            AnswerVoteViewTest._get_votes_sum(answer)
        )

        self.client.login(username='UserB', password='123')
        response = self.client.post(
            reverse('answer-vote-up', kwargs={'answer_id': answer.id})
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(init_votes + 2, response.json()['votes'])
        self.assertEqual(
            init_votes + 2,
            AnswerVoteViewTest._get_votes_sum(answer)
        )

        response = self.client.post(
            reverse('answer-vote-down', kwargs={'answer_id': answer.id})
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(init_votes + 1, response.json()['votes'])
        self.assertEqual(
            init_votes + 1,
            AnswerVoteViewTest._get_votes_sum(answer)
        )

    def test_vote_requires_login(self):
        question = models.Question.objects.filter(title='Title 1').first()
        answer = models.Answer.objects.filter(question__id=question.id).first()

        response = self.client.post(
            reverse('answer-vote-up', kwargs={'answer_id': answer.id})
        )
        self.assertEqual(403, response.status_code, 403)

        response = self.client.post(
            reverse('answer-vote-down', kwargs={'answer_id': answer.id})
        )
        self.assertEqual(403, response.status_code, 403)


class SearchListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        createTestData(question_num=30)

    def test_pagination(self):
        response = self.client.get(reverse('search')+'?q=Title')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('is_paginated' in response.context)
        self.assertTrue(response.context['is_paginated'] == True)
        self.assertEqual(20, len(response.context['question_list']))
        self.assertEqual('Title 1', response.context['question_list'][0].title)
        self.assertEqual('Text 1', response.context['question_list'][0].text)
        self.assertEqual('Title 20', response.context['question_list'][19].title)
        self.assertEqual('Text 20', response.context['question_list'][19].text)

        response = self.client.get(reverse('search')+'?q=Title&page=2')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('is_paginated' in response.context)
        self.assertTrue(response.context['is_paginated'] == True)
        self.assertEqual(10, len(response.context['question_list']))
        self.assertEqual('Title 21', response.context['question_list'][0].title)
        self.assertEqual('Text 21', response.context['question_list'][0].text)
        self.assertEqual('Title 0', response.context['question_list'][9].title)
        self.assertEqual('Text 0', response.context['question_list'][9].text)

    def test_single_search(self):
        response = self.client.get(reverse('search')+'?q=Title 11')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, len(response.context['question_list']))
        self.assertEqual('Title 11', response.context['question_list'][0].title)

    def test_no_result_search(self):
        response = self.client.get(reverse('search')+'?q=ZZZ')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(0, len(response.context['question_list']))

    def test_tag_search_redirection(self):
        response = self.client.get(reverse('search')+'?q=tag:tag1')
        self.assertRedirects(
            response,
            reverse('search_tag', kwargs={'tag': 'tag1'})
        )

    def test_tag_search(self):
        question = models.Question.objects.filter(title='Title 1').first()
        question.save()
        question.tags.create(text='tag1')

        response = self.client.get(
            reverse('search_tag', kwargs={'tag': 'tag1'})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, len(response.context['question_list']))
        self.assertEqual('Title 1', response.context['question_list'][0].title)

    def test_no_result_tag_search(self):
        response = self.client.get(
            reverse('search_tag', kwargs={'tag': 'tag1'})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(0, len(response.context['question_list']))
 