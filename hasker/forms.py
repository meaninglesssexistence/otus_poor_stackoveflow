from django import forms
from django.core.exceptions import ValidationError

from stackoverflow.bootstrapforms import BootstrapFormMixin

from . import models


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
        widgets = {
            'tags': forms.Textarea(attrs={'autocomplete': 'off'})
        }


class AnswerForm(forms.ModelForm):
    class Meta:
        model = models.Answer
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(attrs={'class': "form-control"})
        }
