# -*- coding: utf-8 -*-
"""Классы-формы для создания вопросов и ответов."""

from django import forms
from django.core.exceptions import ValidationError

from stackoverflow.bootstrapforms import BootstrapFormMixin

from . import models


class TagsField(forms.CharField):
    """Поле для отображения и ввода тегов.

    Поле отображает список тегов, как строки, разделенные запятой.
    При сохранении, строка разбивается по запятым и конвертируется в список.
    """

    def to_python(self, value):
        if not value:
            return []
        return [s.strip() for s in value.split(',')]

    def validate(self, value):
        super().validate(value)
        if len(value) > 3:
            raise ValidationError("Provided more then three tags")


class AskForm(BootstrapFormMixin, forms.ModelForm):
    """Форма добавления нового вопроса."""

    tags = TagsField(required=False)

    class Meta:
        model = models.Question
        fields = ('title', 'text')
        widgets = {
            'tags': forms.Textarea(attrs={'autocomplete': 'off'})
        }


class AnswerForm(forms.ModelForm):
    """Форма добавления нового ответа на вопрос."""

    class Meta:
        model = models.Answer
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(attrs={'class': "form-control"})
        }
