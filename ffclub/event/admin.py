# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.encoding import force_unicode
from ffclub.base import admin
from django.contrib.admin import ModelAdmin, StackedInline, TabularInline
from django.contrib.admin.util import unquote
from .models import *
from ffclub.product.models import Order
from ffclub.upload.admin import ImageUploadInline
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.db import transaction
from functools import update_wrapper
from django.db.models import Max, Count
import StringIO
import csv
from django.http import HttpResponse

csrf_protect_m = method_decorator(csrf_protect)


class ParticipationInline(TabularInline):
    model = Participation
    extra = 0


class AwardInline(TabularInline):
    model = Award
    extra = 0


class OrderInline(StackedInline):
    model = Order
    extra = 0


class ActivityAdmin(ModelAdmin):
    change_form_template = 'admin/custom_activity_change_form.html'

    def get_urls(self):
        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            return update_wrapper(wrapper, view)
        urls = super(ActivityAdmin, self).get_urls()
        my_urls = patterns(
            '',
            url(r'^(?P<object_id>\d+)/award/$',
                wrap(self.activity_award_prizes),
                name='admin.activity.award.prizes'),
            url(r'^(?P<object_id>\d+)/export-winners/$',
                wrap(self.activity_export_winners),
                name='admin.activity.export.winners'),
        )
        return my_urls + urls

    @csrf_protect_m
    @transaction.commit_on_success
    def activity_award_prizes(self, request, object_id, extra_context=None):
        opts = self.model._meta
        app_label = opts.app_label

        obj = self.get_object(request, unquote(object_id))
        object_name = force_unicode(opts.verbose_name)
        participations = Participation.objects.filter(activity=obj).prefetch_related('participant', 'participant__person')
        participants = []
        for participation in participations:
            if not participation.participant in participants:
                participants += [participation.participant, ]
        uploads = ImageUpload.objects.filter(
            entity_id=obj.id,
            content_type=ContentType.objects.get_for_model(self.model)).prefetch_related('create_user', 'create_user__person').annotate(Count('votes')).order_by('-votes__count')
        uploaders = []
        uploadIds = []
        for upload in uploads:
            uploadIds += [upload.id, ]
            if not upload.create_user in uploaders:
                uploaders += [upload.create_user, ]
        votes = Vote.objects.filter(
            entity_id__in=uploadIds,
            content_type=ContentType.objects.get(model='imageupload')).prefetch_related('voter', 'voter__person')
        voters = []
        for vote in votes:
            if not vote.voter in voters:
                voters += [vote.voter, ]
        if request.POST:
            award_name = request.POST['award_name']
            #awarded_role = request.POST['awarded_role']
            winner_amount = int(request.POST['winner_amount'])
            #award_type = request.POST['award_type']
            repeat = request.POST['repeat']
            reaward = request.POST['reaward']
            obj_display = force_unicode(obj.title)
            if award_name == u'最高人氣獎':
                if reaward == 'yes':
                    Award.objects.filter(name=u'最高人氣獎', activity=obj).delete()
                    startIndex = 1
                else:
                    startIndex = Award.objects.filter(name=u'最高人氣獎', activity=obj).aggregate(Max('order'))['order__max'] + 1
                awardedWinners = Award.objects.filter(name=u'最高人氣獎', activity=obj).values('winner_id')
                awardedIds = [awardedWinner['winner_id'] for awardedWinner in awardedWinners]
                popUploaders = []
                for upload in uploads:
                    if upload.create_user.id not in awardedIds and upload.create_user not in popUploaders:
                        popUploaders += [upload.create_user, ]
                for index, uploader in enumerate(popUploaders):
                    if index == winner_amount:
                        break
                    award = Award(name=u'最高人氣獎', order=index+startIndex, winner=uploader, activity=obj)
                    award.save()
                self.message_user(request, u'已完成 %s 頒獎！' % award_name)
            elif award_name == u'投票幸運獎':
                if reaward == 'yes':
                    Award.objects.filter(name=u'投票幸運獎', activity=obj).delete()
                    startIndex = 1
                else:
                    startIndex = Award.objects.filter(name=u'投票幸運獎', activity=obj).aggregate(Max('order'))['order__max'] + 1
                if repeat == 'no':
                    awardedWinners = Award.objects.filter(activity=obj).values('winner_id')
                    awardedIds = [awardedWinner['winner_id'] for awardedWinner in awardedWinners]
                    filtered_voters = [voter for voter in voters if voter.id not in awardedIds]
                else:
                    filtered_voters = voters
                from random import shuffle
                shuffle(filtered_voters)
                for index, voter in enumerate(filtered_voters):
                    if index == winner_amount:
                        break
                    award = Award(name=u'投票幸運獎', order=index+startIndex, winner=voter, activity=obj)
                    award.save()
                self.message_user(request, u'已完成 %s 頒獎！' % award_name)
            else:
                self.message_user(request, u'目前不支援此頒獎組合！請選擇正確的得獎角色和頒獎方式。')
        popularAwards = Award.objects.filter(name=u'最高人氣獎', activity=obj).prefetch_related('winner', 'winner__person').order_by('order')
        luckyAwards = Award.objects.filter(name=u'投票幸運獎', activity=obj).prefetch_related('winner', 'winner__person').order_by('order')
        data = {
            'title': '頒獎典禮',
            'object_name': object_name,
            'object': obj,
            'opts': opts,
            'app_label': app_label,
            'participants': participants,
            'uploaders': uploaders,
            'voters': voters,
            'awards': {
                u'最高人氣獎': popularAwards,
                u'投票幸運獎': luckyAwards,
            }
        }
        return render(request, 'admin/activity_award_prizes.html', data)

    @csrf_protect_m
    @transaction.commit_on_success
    def activity_export_winners(self, request, object_id, extra_context=None):
        obj = self.get_object(request, unquote(object_id))
        popularAwards = Award.objects.filter(name=u'最高人氣獎', activity=obj).prefetch_related('winner', 'winner__person').order_by('order')
        luckyAwards = Award.objects.filter(name=u'投票幸運獎', activity=obj).prefetch_related('winner', 'winner__person').order_by('order')
        output = StringIO.StringIO()
        writer = csv.writer(output)
        writer.writerow(['獎項', '順序', '姓名', '暱稱', 'Email', '電話', '地址', '狀態'])
        for popularAward in popularAwards:
            winner = popularAward.winner
            profile = winner.person if hasattr(winner, 'person') else None
            row = ['最高人氣獎', ]
            row += [popularAward.order, ]
            row += [profile.fullname.encode('utf-8') if profile else '%s %s' % (winner.last_name.encode('utf-8'), winner.first_name.encode('utf-8')), ]
            row += [profile.nickname.encode('utf-8') if profile else '']
            row += [winner.email, ]
            row += [profile.phone if profile else '']
            row += [profile.address.encode('utf-8') if profile else '']
            row += [popularAward.status, ]
            writer.writerow(row)
        for luckyAward in luckyAwards:
            winner = luckyAward.winner
            profile = winner.person if hasattr(winner, 'person') else None
            row = ['投票幸運獎', ]
            row += [luckyAward.order, ]
            row += [profile.fullname.encode('utf-8') if profile else '%s %s' % (winner.last_name.encode('utf-8'), winner.first_name.encode('utf-8')), ]
            row += [profile.nickname.encode('utf-8') if profile else '']
            row += [winner.email, ]
            row += [profile.phone if profile else '']
            row += [profile.address.encode('utf-8') if profile else '']
            row += [luckyAward.status, ]
            writer.writerow(row)
        response = HttpResponse(output.getvalue(), mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=every-moment-campaign-awards.csv'
        return response


class EventAdmin(ActivityAdmin):
    search_fields = ['title', 'description', 'location',
                     'orders__usage', 'orders__fullname', 'orders__email',
                     'orders__address', 'orders__occupation', 'orders__feedback']
    list_filter = ['num_of_ppl', 'create_time', 'status', 'orders__create_time', 'orders__status']
    inlines = [AwardInline, OrderInline, ParticipationInline, ImageUploadInline]


admin.site.register(Event, EventAdmin)


class CampaignAdmin(ActivityAdmin):
    search_fields = ['title', 'description']
    list_filter = ['create_time', 'status']
    inlines = [AwardInline, ParticipationInline, ImageUploadInline]


admin.site.register(Campaign, CampaignAdmin)


class VoteAdmin(ModelAdmin):
    search_fields = ['note']
    list_filter = ['vote_time', 'status']


admin.site.register(Vote, VoteAdmin)


class VideoAdmin(ModelAdmin):
    search_fields = ['title', 'description']
    list_filter = ['create_time', 'status']


admin.site.register(Video, VideoAdmin)

class DemoAppAdmin(ModelAdmin):
    search_fields = ['en_title', 'description']
    list_filter = ['create_time', 'status']


admin.site.register(DemoApp, DemoAppAdmin)
