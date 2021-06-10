from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.utils.html import format_html

from . import models
from stackoverflow.bootstrapforms import BootstrapFormMixin

class LoginForm(BootstrapFormMixin, AuthenticationForm):
    ...


class SignUpForm(BootstrapFormMixin, UserCreationForm):
    avatar = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'avatar')


class ImagePreviewWidget(forms.widgets.ClearableFileInput):
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
