from django import template
from django.conf import settings
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce

from ..models import Question


register = template.Library()


@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    query = context['request'].GET.copy()
    query.update(kwargs)
    return query.urlencode()

@register.inclusion_tag('hasker/_trending.html', takes_context=True)
def trending_list(context, num=settings.HASKER_TRENDING_SIZE):
    return {
        'trending_list': Question.objects.annotate(
            votes_sum=Coalesce(Sum('questionvote__vote'), Value(0))
        ).order_by(
            '-votes_sum', '-creation_date'
        ).all()[:num]
    }
