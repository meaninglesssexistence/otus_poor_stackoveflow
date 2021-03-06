# -*- coding: utf-8 -*-
"""Настройки модуля администрирования."""

from django.contrib import admin

from . import models

admin.site.register([
    models.Tag,
    models.Question,
    models.Answer,
    models.QuestionVote,
    models.AnswerVote,
])
