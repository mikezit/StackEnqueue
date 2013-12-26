import datetime
from forum.models import *
from forum import settings
from django.db import models
from forum.utils.mail import send_template_email
from django.core.management.base import NoArgsCommand,BaseCommand
from forum.settings.upload import FLAIR_FOLDER
from django.utils import translation
import subprocess
import logging
import urllib2

cmd = 'xvfb-run --auto-servernum --server-args="-screen 0, 640x480x24" cutycapt --min-width=208 --min-height=58 --url=%(site_base)s/users/user/%(id)s/flair/   --out=%(flair_dir)s/%(id)s.png'

class Command(BaseCommand):
    help="send invitation mail to a user"

    def handle(self, *args, **options):
        users = User.objects.all()
        flair_dir = FLAIR_FOLDER
        if flair_dir[-1] is '/':
            flair_dir = flair_dir[:-1]
        for user in users:
            print user.id  
            try:#test the page is is ok?
                urllib2.urlopen("%s/users/user/%s/flair/" % (settings.APP_URL,user.id)) 
            except :
                print "Error get %s" % user.id
                continue

            _cmd = cmd % {"id":user.id,"flair_dir":flair_dir,"site_base":settings.APP_URL}
            subprocess.call(_cmd,shell=True)
