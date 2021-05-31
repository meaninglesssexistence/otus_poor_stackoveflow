import django
import inspect
from django.test import TestCase

from hasker import forms


class AskFormTest(TestCase):
    def test_valid_form(self):
        form = forms.AskForm(data={
            'title': '123', 'text': '321', 'tags': 'tag1,atg2,tag3'
        })
        self.assertTrue(form.is_valid())

    def test_empty_title(self):
        form = forms.AskForm(data={'title': ' ', 'text': '123'})
        self.assertFalse(form.is_valid())

    def test_empty_text(self):
        form = forms.AskForm(data={'title': '123', 'text': ' '})
        self.assertFalse(form.is_valid())

    def test_too_many_tags(self):
        form = forms.AskForm(data={
            'title': '123', 'text': '321', 'tags': 'tag1,atg2,tag3,tag4'
        })
        self.assertFalse(form.is_valid())


class AnswerFormTest(TestCase):
    def test_valid_form(self):
        form = forms.AnswerForm(data={'text': '123'})
        self.assertTrue(form.is_valid())

    def test_empty_text(self):
        form = forms.AnswerForm(data={'text': ' '})
        self.assertFalse(form.is_valid())


class SignUpFormTest(TestCase):
    def test_valid_form(self):
        form = forms.SignUpForm(data={
            'username': 'john',
            'email': 'john@example.com',
            'password1': 'Qwe456#$',
            'password2': 'Qwe456#$'
        })
        self.assertTrue(form.is_valid())

    def test_weak_password(self):
        form = forms.SignUpForm(data={
            'username': 'john',
            'email': 'john@example.com',
            'password1': '123',
            'password2': '123'
        })
        self.assertFalse(form.is_valid())

    def test_avatar_field(self):
        form = forms.SignUpForm(data={
            'username': 'john',
            'email': 'john@example.com',
            'password1': 'Qwe456#$',
            'password2': 'Qwe456#$'
        })
        self.assertIsNotNone(form.fields['avatar'])


class SettingsFormTest(TestCase):
    def test_valid_form(self):
        form = forms.SettingsForm(data={
            'username': 'john',
            'email': 'john@example.com'
        })
        self.assertTrue(form.is_valid())

    def test_empty_email(self):
        form = forms.SettingsForm(data={
            'username': 'john',
            'email': ' ',
        })
        self.assertTrue(form.is_valid())

    def test_invalid_email(self):
        form = forms.SettingsForm(data={
            'username': 'john',
            'email': '123',
        })
        self.assertFalse(form.is_valid())

    def test_avatar_field(self):
        form = forms.SettingsForm(data={
            'username': 'john',
            'email': 'john@example.com'
        })
        self.assertIsNotNone(form.fields['avatar'])
        self.assertHTMLEqual(
            """<img class="preview" src="/static/no-avatar.png">
               <br>
               <input accept="image/*" class="form-control" name="avatar" type="file">
            """,
            form.fields['avatar'].widget.render('avatar', None)
        )


class AllFormsTest(TestCase):
    def test_fields_css_class(self):
        form_classes = inspect.getmembers(
            forms,
            lambda x: inspect.isclass(x) and (
                issubclass(x, django.forms.Form) or \
                issubclass(x, django.forms.ModelForm)
            ) and (inspect.getmodule(x) == forms)
        )

        for (_, form_class) in form_classes:
            form = form_class()
            for field in form.fields.values():
                self.assertEqual(
                    'form-control',
                    field.widget.attrs.get('class')
                )
