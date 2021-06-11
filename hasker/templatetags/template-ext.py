# -*- coding: utf-8 -*-
"""Несколько кастомных тегов для использования в шаблонах."""

from django import template
from django.conf import settings
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce

from ..models import Question


register = template.Library()


@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    """Добавляет пары ключ/значение из kwargs к параметрам запроса.

    Используется, например для формирования ссылки на следующую
    страницу с сохранением параметров запроса, присутствующих
    в URL-е.

    Examples:
        href="?{% url_replace page=1 %}
    """
    query = context['request'].GET.copy()
    query.update(kwargs)
    return query.urlencode()

@register.inclusion_tag('hasker/_trending.html', takes_context=True)
def trending_list(context, num=settings.HASKER_TRENDING_SIZE):
    """Выводит список запросов "в тренде".

    Examples:
        {% load template-ext %}
        {% trending_list %}
    """
    return {
        'trending_list': Question.objects.annotate(
            votes_sum=Coalesce(Sum('questionvote__vote'), Value(0))
        ).order_by(
            '-votes_sum', '-creation_date'
        ).all()[:num]
    }
