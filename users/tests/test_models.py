# -*- coding: utf-8 -*-
"""Тесты для классов-моделей."""

from datetime import datetime
from django.contrib.auth.models import User
from django.test import TestCase

from users import models


class UserAvatarTest(TestCase):
    def test_avatar_creation_on_user_creation(self):
        user = User.objects.create_user('john', 'john@example.com', '123')
        avatars = models.UserAvatar.objects.all()

        self.assertEqual(1, len(avatars))
        self.assertFalse(avatars[0].avatar)

    def test_avatar_removing_on_user_removing(self):
        user = User.objects.create_user('john', 'john@example.com', '123')

        avatars = models.UserAvatar.objects.all()
        self.assertEqual(1, len(avatars))

        user.delete()

        avatars = models.UserAvatar.objects.all()
        self.assertEqual(0, len(avatars))
