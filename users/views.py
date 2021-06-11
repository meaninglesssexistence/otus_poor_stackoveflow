# -*- coding: utf-8 -*-
"""Обработчики запросов."""

from django import urls
from django.contrib.auth import login, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.views.generic.edit import FormView

from .forms import LoginForm, SignUpForm, SettingsForm

class LoginFormView(LoginView):
    """Обработка запроса на логин пользователя."""

    template_name = 'users/login.html'
    form_class = LoginForm


class SignupFormView(FormView):
    """Обработка запроса на создание нового пользователя.

    После успешного создания пользователя осуществляется его логин.
    """

    template_name = 'users/signup.html'
    form_class = SignUpForm
    success_url = urls.reverse_lazy('index')

    def form_valid(self, form):
        # Create new user
        user = form.save()
        user.refresh_from_db()
        user.useravatar.avatar = form.cleaned_data.get('avatar')
        user.save()
        password = form.cleaned_data.get('password1')
        # Login new user
        user = authenticate(username=user.username, password=password)
        login(self.request, user)
        return super().form_valid(form)


class SettingsFormView(LoginRequiredMixin, FormView):
    """Обработка запроса на изменение настроек пользователя."""

    template_name = 'users/settings.html'
    form_class = SettingsForm
    success_url = urls.reverse_lazy('index')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.useravatar.avatar = form.cleaned_data.get('avatar')
        user.save()
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.request.user
        kwargs['initial'] = {'avatar': self.request.user.useravatar.avatar}
        return kwargs
