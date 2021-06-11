# -*- coding: utf-8 -*-
"""Маршрутизация URL-ов для приложения."""

from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views


urlpatterns = [
    path('login/', views.LoginFormView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('signup/', views.SignupFormView.as_view(), name='signup'),
    path('settings/', views.SettingsFormView.as_view(), name='settings'),
]
