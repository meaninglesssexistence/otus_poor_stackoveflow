# -*- coding: utf-8 -*-
"""Маршрутизация URL-ов для приложения."""

from django.urls import path

from . import views
from . import rest


urlpatterns = [
    path('', views.QuestionListView.as_view(), name='index'),

    # Отображение звопроса.
    path('question/<int:question_id>/',
         views.QuestionView.as_view(),
         name='question'),
    # Голосование за вопрос.
    path('question/<int:question_id>/vote-up/',
         rest.QuestionVoteView.as_view(),
         name='question-vote-up',
         kwargs={'is_up': True}),
    # Голосование против вопроса.
    path('question/<int:question_id>/vote-down/',
         rest.QuestionVoteView.as_view(),
         name='question-vote-down',
         kwargs={'is_up': False}),

    # Установка пометки верного ответа.
    path('question/solution-set/<int:answer_id>/',
         rest.MarkSolutionView.as_view(),
         name='solution-set',
         kwargs={'is_set': True}),
    # Снятие пометки верного ответа.
    path('question/solution-clear/<int:answer_id>/',
         rest.MarkSolutionView.as_view(),
         name='solution-clear',
         kwargs={'is_set': False}),

    # Новый вопрос.
    path('question/ask/', views.AskFormView.as_view(), name='ask'),

    # Голосование за ответ.
    path('answer/<int:answer_id>/vote-up/',
         rest.AnswerVoteView.as_view(),
         name='answer-vote-up',
         kwargs={'is_up': True}),
    # Голосование против ответа.
    path('answer/<int:answer_id>/vote-down/',
         rest.AnswerVoteView.as_view(),
         name='answer-vote-down',
         kwargs={'is_up': False}),

    # Поиск по тексту.
    path('search/',
         views.SearchListView.as_view(template_name='hasker/search-txt.html'),
         name='search'),
    # Поиск по тегу.
    path('tag/<str:tag>/',
         views.SearchListView.as_view(template_name='hasker/search-tag.html'),
         name='search_tag'),
]
