from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views
from . import rest


urlpatterns = [
    path('', views.QuestionListView.as_view(), name='index'),

    path('question/<int:question_id>/',
         views.QuestionView.as_view(),
         name='question'),
    path('question/<int:question_id>/vote-up/',
         rest.QuestionVoteView.as_view(),
         name='question-vote-up',
         kwargs={'is_up': True}),
    path('question/<int:question_id>/vote-down/',
         rest.QuestionVoteView.as_view(),
         name='question-vote-down',
         kwargs={'is_up': False}),

    path('question/solution-set/<int:answer_id>/',
         rest.MarkSolutionView.as_view(),
         name='solution-set',
         kwargs={'is_set': True}),
    path('question/solution-clear/<int:answer_id>/',
         rest.MarkSolutionView.as_view(),
         name='solution-clear',
         kwargs={'is_set': False}),

    path('question/ask/', views.AskFormView.as_view(), name='ask'),

    path('answer/<int:answer_id>/vote-up/',
         rest.AnswerVoteView.as_view(),
         name='answer-vote-up',
         kwargs={'is_up': True}),
    path('answer/<int:answer_id>/vote-down/',
         rest.AnswerVoteView.as_view(),
         name='answer-vote-down',
         kwargs={'is_up': False}),

    path('login/', views.LoginFormView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('signup/', views.SignupFormView.as_view(), name='signup'),
    path('settings/', views.SettingsFormView.as_view(), name='settings'),

    path('search/',
         views.SearchListView.as_view(template_name='hasker/search-txt.html'),
         name='search'),
    path('tag/<str:tag>/',
         views.SearchListView.as_view(template_name='hasker/search-tag.html'),
         name='search_tag'),
]
