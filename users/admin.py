# -*- coding: utf-8 -*-
"""Настройки модуля администрирования."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from . import models


class UserAvatarInline(admin.StackedInline):
    model = models.UserAvatar
    can_delete = False
    verbose_name_plural = 'user'


class UserAdmin(BaseUserAdmin):
    inlines = (UserAvatarInline,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register([
    models.UserAvatar,
])
