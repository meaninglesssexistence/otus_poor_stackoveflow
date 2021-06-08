from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.html import format_html

from . import models


class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs.update({'class': 'form-control'})


class TagsField(forms.CharField):
    def to_python(self, value):
        if not value:
            return []
        return [s.strip() for s in value.split(',')]

    def validate(self, value):
        super().validate(value)
        if len(value) > 3:
            raise ValidationError("Provided more then three tags")


class AskForm(BootstrapFormMixin, forms.ModelForm):
    tags = TagsField(required=False)

    class Meta:
        model = models.Question
        fields = ('title', 'text')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tags'].widget.attrs.update({'autocomplete': 'off'})


class AnswerForm(forms.Form):
    text = forms.CharField(label='Text', max_length=2048,
                           widget=forms.Textarea(
                               attrs={'class': "form-control"}
                           ))


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
