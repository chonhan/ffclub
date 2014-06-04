# -*- coding: utf-8 -*-
from datetime import datetime
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from django.db import models
from django.contrib.contenttypes import generic
from ffclub.settings import ALL_ORDER_DETAIL_CHOICES
from ffclub.event.models import Activity
from ffclub.upload.models import ImageUpload


class Product(models.Model):
    title = models.CharField(max_length=255, verbose_name='品名')
    description = models.CharField(max_length=255, verbose_name='描述')
    quantity = models.IntegerField(verbose_name='數量')
    photos = generic.GenericRelation(ImageUpload, content_type_field='content_type', object_id_field='entity_id')
    create_user = models.ForeignKey(User, related_name='+')
    create_time = models.DateTimeField(default=datetime.now)
    update_user = models.ForeignKey(User, related_name='+')
    update_time = models.DateTimeField(default=datetime.now)
    status = models.CharField(max_length=20,
                              choices=(('normal', '正常'), ('lack', '庫存不足')),
                              default='normal')
    type = models.CharField(max_length=20,
                            choices=(('souvenir', '宣傳品'), ('design', '設計品')),
                            default='souvenir')

    def get_absolute_url(self):
        return reverse('product.photos', kwargs={'product_id': self.id})

    def __unicode__(self):
        return unicode('[%s] %s (%d)' % (self.type, self.title, self.quantity))

    class Meta:
        verbose_name = verbose_name_plural = '宣傳品'


class Order(models.Model):
    usage = models.TextField(max_length=512, verbose_name='預計推廣對象 以及 將如何使用 Firefox 活力宣傳物(*)',
                             help_text='申請審核通過後，我們會將宣傳品寄送給你，請確認以下收件人資料:')
    fullname = models.CharField(max_length=255, verbose_name='姓名(*)')
    email = models.EmailField(verbose_name='電子郵件(*)', help_text='目前僅提供台灣本島及外島寄送服務，國際郵件暫不受理。')
    address = models.CharField(max_length=255, verbose_name='寄送地址(*)')
    occupation = models.CharField(max_length=255, verbose_name='職業(*)')
    feedback = models.TextField(max_length=512, verbose_name='其它建議', blank=True, default='')

    create_user = models.ForeignKey(User, related_name='+')
    create_time = models.DateTimeField(default=datetime.now, verbose_name='Order create time')
    event = models.ForeignKey(Activity, related_name='orders')
    products = models.ManyToManyField(Product, related_name='+', through='OrderDetail')
    status = models.CharField(max_length=20,
                              choices=(('wait_for_confirm', '待確認'), ('confirmed', '已確認'),
                                       ('processing', '處理中'), ('processed', '已處理'), ('spam', '垃圾')),
                              default='wait_for_confirm', verbose_name='Order status')

    def __unicode__(self):
        return unicode('%s (%s) | %s | %s' % (self.event.title, self.status, self.fullname, self.address))

    class Meta:
        verbose_name = verbose_name_plural = '訂單'


class OrderDetail(models.Model):
    description = models.CharField(max_length=255, blank=True, default='')
    quantity = models.IntegerField(choices=ALL_ORDER_DETAIL_CHOICES,
                                   default=0, verbose_name='數量')
    order = models.ForeignKey(Order, related_name='details')
    product = models.ForeignKey(Product, related_name='+')

    def __unicode__(self):
        return unicode('%s -> %s (%d)' % (self.order.event.title, self.product.title, self.quantity))

    class Meta:
        verbose_name = verbose_name_plural = '訂單細節'


class OrderVerification(models.Model):
    code = models.CharField(max_length=255)
    create_user = models.ForeignKey(User, related_name='+')
    create_time = models.DateTimeField(default=datetime.now, verbose_name='Verification create time')
    status = models.CharField(max_length=20,
                              choices=(('issued', '待確認'), ('confirmed', '已確認')),
                              default='issued', verbose_name='Verification status')
    order = models.ForeignKey(Order, related_name='verification')

    def __unicode__(self):
        return unicode('%s (%s)' % (self.order.event.title, self.status))

    class Meta:
        verbose_name = verbose_name_plural = '訂單確認'
