# -*- coding: utf-8 -*-
from django.core.validators import RegexValidator
from django.db import models
# from django.contrib.auth.models import User


# class CustomUser(User):
#
#     def __unicode__(self):
#         return self.email
#
#     class Meta:
#         proxy = True
#         verbose_name = verbose_name_plural = '使用者'
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from datetime import datetime
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from ffclub import settings


class Person(models.Model):
    user = models.OneToOneField(User, primary_key=True, unique=True)
    nickname = models.CharField(max_length=255, verbose_name='暱稱', blank=True)
    email = models.EmailField(verbose_name='Email', blank=True)
    fullname = models.CharField(max_length=255, verbose_name='姓名(*)', blank=True)
    gender = models.CharField(max_length=7, verbose_name='性別(*)',
                              choices=(('unknown', '未指定'), ('male', '男性'), ('female', '女性')), default='unknown')
    phone = models.CharField(max_length=255, verbose_name='聯絡電話(*)', blank=True,
                             validators=[RegexValidator('^\+?[-0-9\s]*(\([-0-9\s]+\))?[-0-9\s]+$')])
    address = models.CharField(max_length=255, verbose_name='地址(*)', blank=True)
    occupation = models.CharField(max_length=255, verbose_name='職業(*)', blank=True)
    education = models.CharField(max_length=255, verbose_name='學歷', blank=True,
                                 choices=(('graduate_school', '研究所'), ('college', '大學'), ('specialized_school', '專科'), ('highschool', '高中')), default='')
    birthday = models.DateTimeField(blank=True, null=True, verbose_name='生日')
    status = models.CharField(max_length=20,
                              choices=(('normal', '正常'), ('spam', '垃圾')),
                              default='normal')
    subscribing = models.BooleanField(default=True, verbose_name='我願意訂閱 Mozilla 電子報')

    def __unicode__(self):
        return unicode('%s (%s)' % (self.fullname, self.status))

    class Meta:
        verbose_name = verbose_name_plural = '個人資料'


class Metadata(models.Model):
    name = models.CharField(max_length=255, blank=True, default='')
    type = models.CharField(max_length=20,
                            choices=(('number', '數字'), ('string', '字串'),
                                     ('datetime', '日期時間'), ('file', '檔案')),
                            default='string')
    index = models.PositiveIntegerField()

    create_user = models.ForeignKey(User, related_name='+')
    create_time = models.DateTimeField(default=datetime.now)

    owner = models.ForeignKey(User, related_name='metadata')

    def __unicode__(self):
        return unicode('%s = %s' % (self.name, self.value))

    class Meta:
        verbose_name = verbose_name_plural = '個人資料擴充欄位'


class MetaString(Metadata):
    value = models.CharField(max_length=255, blank=True, default='', verbose_name='字串')


class MetaNumber(Metadata):
    value = models.FloatField(default=0.0, verbose_name='數字')


class MetaDatetime(Metadata):
    value = models.DateTimeField(default=datetime.now, verbose_name='時間')


class MetaFile(Metadata):
    value = models.FileField(upload_to=settings.FILE_PATH, max_length=255, db_index=True, verbose_name='檔案')


# User.profile = property(lambda u: Person.objects.get_or_create(user=u)[0])
@receiver(pre_save, sender=Person)
def sync_person_default_email(sender, instance, **kwargs):
    if not instance.email:
        instance.email = instance.user.email
    if not instance.fullname:
        instance.fullname = instance.user.first_name + instance.user.last_name

@receiver(post_save, sender=User)
@receiver(post_save, sender=Person)
def manage_subscription(sender, instance, **kwargs):
    pass