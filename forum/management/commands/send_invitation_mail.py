import datetime
from forum.models import *
from forum import settings
from django.db import models
from forum.utils.mail import send_template_email
from django.core.management.base import NoArgsCommand,BaseCommand
from forum.settings.email import EMAIL_DIGEST_FLAG
from django.utils import translation
import logging

class Recipient:
    def __init__(self,email):
        name = email.split("@")[0]
        self.username = name
        self.email = email
        self.type = "invitation"
        
class Command(BaseCommand):
    help="send invitation mail to a user"

    def handle(self, *args, **options):
        if len(args) == 0 :
            logging.error("require email arg!")
            return

        recipients = []

        for email in args:
            recipient = Recipient(email)
            recipients.append(recipient)

        logging.log(2,"send invitation email to %s" % email)
        return send_template_email(recipients,"notifications/invitation.html",locals())


        
