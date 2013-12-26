import datetime
from forum.models import *
from forum import settings
from django.db import models
from forum.utils.mail import send_template_email
from django.core.management.base import NoArgsCommand,BaseCommand
from forum.settings.email import EMAIL_DIGEST_FLAG
from django.utils import translation
import logging

class Command(BaseCommand):
    help="send invitation mail to a user"

    def handle(self, *args, **options):

        #Users = User.objects.filter(password='!')
        Users = User.objects.all()[0:1]
        #logging.log(2,"send invitation email to %s" % email)
        send_template_email(Users,"notifications/domain_change_notify.html",locals())


        
