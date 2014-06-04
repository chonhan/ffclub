# -*- coding: utf-8 -*-

from datetime import datetime
import commonware.log

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.db import models
from django.utils.encoding import iri_to_uri
# from ffclub.event.models import Vote
from ffclub.settings import MEDIA_URL, SITE_URL, MEDIA_ROOT

from utils import *

log = commonware.log.getLogger('ffclub')


class ImageUpload(models.Model):
    """An image uploaded to an object using content type generic links."""

    usage = models.CharField(max_length=20,
                             choices=(('original', '原始圖'), ('preview', '預覽圖'), ('mobile', '行動版')),
                             default='original')

    description = models.CharField(max_length=255, verbose_name='相片說明(*)')

    link = models.URLField(verbose_name='超連結', default='', blank=True)
    link_text = models.CharField(max_length=255, verbose_name='連結文字', default='', blank=True)

    link2 = models.URLField(verbose_name='超連結2', default='', blank=True)
    link2_text = models.CharField(max_length=255, verbose_name='連結文字2', default='', blank=True)

    status = models.CharField(max_length=20,
                              choices=(('normal', '正常'), ('reported', '被檢舉'), ('spam', '垃圾')),
                              default='normal')

    image_large = models.ImageField(upload_to=settings.FILE_PATH,
                                    width_field='image_large_width', height_field='image_large_height',
                                    max_length=255, db_index=True, verbose_name='相片檔案(*)')

    create_user = models.ForeignKey(User, related_name='+')
    create_time = models.DateTimeField(default=datetime.now)

    content_type = models.ForeignKey(ContentType, related_name='images')
    entity_id = models.PositiveIntegerField()
    entity_object = generic.GenericForeignKey('content_type', 'entity_id')

    votes = generic.GenericRelation('event.Vote', content_type_field='content_type', object_id_field='entity_id')

    # Generated thumbnails
    image_medium = models.ImageField(upload_to=settings.FILE_PATH + '/m',
                                     width_field='image_medium_width', height_field='image_medium_height',
                                     max_length=255, db_index=True, null=True, blank=True)

    image_small = models.ImageField(upload_to=settings.FILE_PATH + '/s',
                                    width_field='image_small_width', height_field='image_small_height',
                                    max_length=255, db_index=True, null=True, blank=True)

    # Generated values
    image_large_width = models.IntegerField(null=True, blank=True)
    image_large_height = models.IntegerField(null=True, blank=True)

    image_medium_width = models.IntegerField(null=True, blank=True)
    image_medium_height = models.IntegerField(null=True, blank=True)

    image_small_width = models.IntegerField(null=True, blank=True)
    image_small_height = models.IntegerField(null=True, blank=True)

    def save(self):
        if self.id is None:
            image_name = self.image_large.name
            content_type = self.image_large.file.content_type
            image_stream = open_image(self.image_large)
            rotate_degree = 0
            try:
                exif = image_stream._getexif()
                if exif and 0x0112 in exif:
                    orientation = exif[0x0112]
                    log.debug('Orientation: %d' % orientation)
                    if orientation == 6:
                        rotate_degree = -90
                        self.image_large_width, self.image_large_height = self.image_large_height, self.image_large_width
                    if orientation == 3:
                        rotate_degree = 180
                    if orientation == 8:
                        rotate_degree = 90
                        self.image_large_width, self.image_large_height = self.image_large_height, self.image_large_width
            except AttributeError:
                log.debug('No EXIF found!')

            log.debug('Content Type: ' + content_type)

            cropped = hasattr(self, 'aspectRatio') and hasattr(self, 'dragLeft') and hasattr(self, 'dragTop')

            large_size = compute_new_size((self.image_large_width, self.image_large_height),
                                          LARGE_SIZE, RESIZE_MODE_ASPECT_FILL)
            large_crop_box = compute_crop_box(self.aspectRatio, large_size, (self.frameWidth, self.frameHeight),
                                              (self.dragLeft, self.dragTop)) if cropped else None
            large_image = resize_image(image_name, image_stream,
                                       large_size, content_type, rotate_degree, large_crop_box)

            medium_size = compute_new_size((self.image_large_width, self.image_large_height),
                                           MEDIUM_SIZE, RESIZE_MODE_ASPECT_FIT)
            medium_crop_box = compute_crop_box(self.aspectRatio, medium_size, (self.frameWidth, self.frameHeight),
                                               (self.dragLeft, self.dragTop)) if cropped else None
            medium_image = resize_image(image_name, image_stream,
                                        medium_size, content_type, rotate_degree, medium_crop_box)

            small_size = compute_new_size((self.image_large_width, self.image_large_height),
                                          SMALL_SIZE, RESIZE_MODE_ASPECT_FIT)
            small_crop_box = compute_crop_box(self.aspectRatio, small_size, (self.frameWidth, self.frameHeight),
                                              (self.dragLeft, self.dragTop)) if cropped else None
            small_image = resize_image(image_name, image_stream,
                                       small_size, content_type, rotate_degree, small_crop_box)

            self.image_medium.save(medium_image.name, medium_image, save=False)
            self.image_large.save(large_image.name, large_image, save=False)
            self.image_small.save(small_image.name, small_image, save=False)

        return super(ImageUpload, self).save()

    def get_share_image(self):
        if hasattr(self.entity_object, 'slug') and self.content_type.model == 'campaign':
            return open('%s/%s%s/%ld.%s' % (MEDIA_ROOT, SHARE_FILE_PATH, self.entity_object.slug, self.id,
                                            self.image_large.name.split('.')[-1]), 'r')
        else:
            return self.image_large

    def get_absolute_url(self):
        return reverse('activity.photo', kwargs={'type': self.content_type.model, 'photo_id': self.id})

    def get_absolute_share_url(self):
        if hasattr(self.entity_object, 'slug') and self.content_type.model == 'campaign':
            return reverse('campaign.photo', kwargs={'slug': self.entity_object.slug, 'photo_id': self.id})
        else:
            return self.get_absolute_url()

    def get_share_path(self):
        if hasattr(self.entity_object, 'slug'):
            return '%s%s/%ld.%s' % (SHARE_FILE_PATH, self.entity_object.slug, self.id,
                                    self.image_large.name.split('.')[-1])
        else:
            return self.get_large_path()

    def get_large_path(self):
        return iri_to_uri(self.image_large.name)

    def get_medium_path(self):
        return iri_to_uri(self.image_medium.name)

    def get_small_path(self):
        return iri_to_uri(self.image_small.name)

    def __unicode__(self):
        return u'%s -> %s: %s (%s)' % (self.entity_object, self.image_large.name, self.usage, self.status)

    class Meta:
        verbose_name = verbose_name_plural = '圖片上傳'
