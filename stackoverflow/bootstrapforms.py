# -*- coding: utf-8 -*-
"""Вспомогательные классы для использования Bootstrap в формах."""

class BootstrapFormMixin:
    """Класс-mixin для происвоения полям формы CSS-аттрибута form-control.

    Example:
        class AskForm(BootstrapFormMixin, forms.ModelForm):
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs.update({'class': 'form-control'})
