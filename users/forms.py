# -*- coding: utf-8 -*-
"""Классы-формы для работы с пользователем."""

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.utils.html import format_html

from . import models
from stackoverflow.bootstrapforms import BootstrapFormMixin

class LoginForm(BootstrapFormMixin, AuthenticationForm):
    """Форма логина.

    Используется стандартная форма AuthenticationForm.
    Класс BootstrapFormMixin подключает Bootstrap для ее отображения.
    """
    ...


class SignUpForm(BootstrapFormMixin, UserCreationForm):
    """Форма добавления нового пользователя.

    Используется стандартная форма UserCreationForm.
    Класс BootstrapFormMixin подключает Bootstrap для ее отображения.
    Добавляетсся поле avatar для работы с аватаркой пользователя.
    """

    avatar = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'avatar')


class ImagePreviewWidget(forms.widgets.ClearableFileInput):
    """Виджет для отображения аватарки пользователя.

    Если у пользователя указан аватар, выводится он. Если нет, выводится
    стандартное изображение.
    """

    def render(self, name, value, attrs=None, **kwargs):
        input_html = super().render(name, value, attrs, **kwargs)
        if value:
            img_html = format_html(
                '<img class="preview" src="{}"/>', value.url)
        else:
            img_html = format_html(
                '<img class="preview" src="/static/img/no-avatar.png"/>', '')

        return f'{img_html}<br/>{input_html}'


class SettingsForm(BootstrapFormMixin, forms.ModelForm):
    """Форма изменения настроек пользователя."""

    avatar = forms.ImageField(required=False, widget=ImagePreviewWidget)

    class Meta:
        model = User
        fields = ('username', 'email', 'avatar')
        labels = {'username': 'Login'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Делаем поле non-required, потому что read-only
        # поля не передаются браузером обратно на сервер.
        self.fields['username'].required = False
        self.fields['username'].disabled = True
