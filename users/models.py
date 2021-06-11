# -*- coding: utf-8 -*-
"""Классы-модели для работы с пользователями."""

from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.templatetags.static import static

class UserAvatar(models.Model):
    """Модель для хранения аватарки пользоывателя.

    Класс связан отношением one-to-one со стандартным классом User.
    """

    avatar = models.ImageField(blank=True, upload_to='avatars')
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    @property
    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return static('img/no-avatar.png')

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def update_useravatar_signal(sender, instance, created, **kwargs):
    """Перехватчик создания модели User.

    При создании новой модели User для нее создается экземпляр
    модели UserAvatar.
    """

    if created:
        UserAvatar.objects.create(user=instance)
    instance.useravatar.save()
