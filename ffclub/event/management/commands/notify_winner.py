# -*- coding: utf-8 -*-
from optparse import make_option
from django.core.mail import EmailMultiAlternatives
from email.errors import MessageError
from email.mime.text import MIMEText
from time import sleep
from django.core.management.base import BaseCommand
from email.header import Header
import sys
import premailer
import commonware.log
from BeautifulSoup import BeautifulSoup

log = commonware.log.getLogger('newsletter')


class Unbuffered:

    def __init__(self, stream):
        self.stream = stream

    def write(self, data):
        self.stream.write(data)
        self.stream.flush()

    def __getattr__(self, attr):
        return getattr(self.stream, attr)


class Command(BaseCommand):
    help = 'Notify winners'
    option_list = BaseCommand.option_list + (
        make_option('--attach-markup-file', action='store_true', dest='attach-markup-file', default=False,
                    help='Attach the HTML Markup as a downloadable file.'),
    )

    def handle(self, *args, **options):
        self.options = options
        attachments = []
        testing = True if 1 < len(args) else False
        sys.stdout = Unbuffered(sys.stdout)
        template = args[0]
        from_email = '"Mozilla Taiwan" <no-reply@mozilla.com.tw>'
        with open('%s.txt' % template) as file:
            text_content = file.read().decode('utf-8')
            file.close()
        with open('%s.html' % template) as file:
            html_content = file.read().decode('utf-8')
            if options['attach-markup-file']:
                attachments[0] = MIMEText(html_content, _subtype='text/html', _charset='utf-8')
                attachments[0].add_header('Content-Disposition', 'attachment', filename='%s.html' % template)
            file.close()
        soup = BeautifulSoup(html_content)
        subject = Header(soup.title.string.encode('utf8'), 'utf-8')
        mail_content = premailer.transform(html_content)
        # headers = {'Reply-To': 'mozilla-tw@mozilla.com'}
        headers = {}
        # charset = 'utf-8'
        if not testing:
            with open('subscriptions.txt') as file:
                subscriptions = file.readlines()
                for subscription in subscriptions:
                    self.send_mail(subject, headers, from_email, (subscription.rstrip(), ),
                                   text_content, mail_content, attachments)
                    sleep(10)
        elif '@' in args[1]:
            self.send_mail(subject, headers, from_email, (args[1], ), text_content, mail_content, attachments)
        else:
            with open(args[1]) as file:
                subscriptions = file.readlines()
                for subscription in subscriptions:
                    self.send_mail(subject, headers, from_email, (subscription.rstrip(), ),
                                   text_content, mail_content, attachments)
                    sleep(10)

    def send_mail(self, subject, headers, from_email, to_mail, text_content, mail_content, attachments):
        mail = EmailMultiAlternatives(subject=subject, body=text_content, headers=headers,
                                      from_email=from_email, to=to_mail)
        mail.attach_alternative(mail_content, 'text/html')
        for attachment in attachments:
            mail.attach(attachment)
        try:
            mail.send()
            print('Sent mail to %s.' % to_mail)
        except MessageError as e:
            print('Failed to send to %s.' % to_mail, e)
        except RuntimeError as e:
            print('Unexpected error when sending to %s.' % to_mail, e)

    @staticmethod
    def named(email, name):
        if name:
            return '%s <%s>' % (name, email)
        return email
