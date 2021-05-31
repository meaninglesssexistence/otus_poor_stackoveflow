import django.utils
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserAvatar(models.Model):
    avatar = models.ImageField(blank=True, upload_to='avatars')
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def update_useravatar_signal(sender, instance, created, **kwargs):
    if created:
        UserAvatar.objects.create(user=instance)
    instance.useravatar.save()


class Tag(models.Model):
    text = models.CharField(max_length=32)

    def __str__(self):
        return self.text


class Question(models.Model):
    title = models.CharField(max_length=128)
    text = models.TextField(max_length=2048)
    creation_date = models.DateTimeField(default=django.utils.timezone.now)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tag1 = models.ForeignKey(Tag, blank=True, null=True,
                             on_delete=models.SET_NULL,
                             related_name='question_tags1')
    tag2 = models.ForeignKey(Tag, blank=True, null=True,
                             on_delete=models.SET_NULL,
                             related_name='question_tags2')
    tag3 = models.ForeignKey(Tag, blank=True, null=True,
                             on_delete=models.SET_NULL,
                             related_name='question_tags3')

    @property
    def tags(self):
        tag_list = []
        if self.tag1:
            tag_list.append(self.tag1)
        if self.tag2:
            tag_list.append(self.tag2)
        if self.tag3:
            tag_list.append(self.tag3)
        return tag_list

    def __str__(self):
        return self.title


class Answer(models.Model):
    text = models.TextField(max_length=2048)
    creation_date = models.DateTimeField(default=django.utils.timezone.now)
    correct = models.BooleanField(default=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    def __str__(self):
        return self.text


class QuestionVote(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE
    )
    vote = models.SmallIntegerField(
        default=0,
        validators=[
            MaxValueValidator(1),
            MinValueValidator(-1)
        ])


class AnswerVote(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    answer = models.ForeignKey(
        Answer,
        on_delete=models.CASCADE
    )
    vote = models.SmallIntegerField(
        default=0,
        validators=[
            MaxValueValidator(1),
            MinValueValidator(-1)
        ])
