from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.templatetags.static import static

class UserAvatar(models.Model):
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
    if created:
        UserAvatar.objects.create(user=instance)
    instance.useravatar.save()
