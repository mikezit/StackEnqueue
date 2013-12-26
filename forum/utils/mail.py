import email
import socket
import os
import logging

try:
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.image import MIMEImage
    from email.header import Header
except:
    from email.MIMEMultipart import MIMEMultipart
    from email.MIMEText import MIMEText
    from email.MIMEImage import MIMEImage
    from email.Header import Header

from django.core.mail import DNS_NAME
from django.core.mail import EmailMultiAlternatives
from django.core.mail import send_mail
from smtplib import SMTP
from forum import settings
from django.template import loader, Context, Template
from forum.utils.html import sanitize_html
from forum.context import application_settings
from forum.utils.html2text import HTML2Text
from threading import Thread

def send_template_email(recipients, template, context):
    t = loader.get_template(template)
    context.update(dict(recipients=recipients, settings=settings))
    t.render(Context(context))

def create_and_send_mail_messages(messages):
    if settings.USE_SES:
        _send_mail_by_ses(messages)
    else:
        _send_mail_by_smtp(messages)

def _send_mail_by_ses(messages):
    if not settings.EMAIL_HOST:
        return

    if len(messages) == 0:
        return

    is_invitate=False
    sender = Header(unicode(settings.APP_SHORT_NAME), 'utf-8')
    sender.append('<%s>' % unicode(settings.DEFAULT_FROM_EMAIL))
    sender = u'%s <%s>' % (unicode(settings.APP_SHORT_NAME), unicode(settings.DEFAULT_FROM_EMAIL))

    try:
        index = 0
        connection = None
        for recipient, subject, html, text, media in messages:

            if sender is None:
                sender = str(settings.DEFAULT_FROM_EMAIL)
                
            if hasattr(messages[0][0],"type") and messages[0][0].type == "invitation":
                is_invitate=True

            print ">>>",recipient.email," ",index
            index += 1

            msg = EmailMultiAlternatives(subject, from_email=sender,to=[recipient.email])
            msg.preamble = 'This is a multi-part message from %s.' % unicode(settings.APP_SHORT_NAME).encode('utf8')

            msgAlternative = MIMEMultipart('alternative')
            msg.attach(msgAlternative)

            msgAlternative.attach(MIMEText(text.encode('utf-8'), _charset='utf-8'))
            msgAlternative.attach(MIMEText(html.encode('utf-8'), 'html', _charset='utf-8'))
            for alias, location in media.items():
                fp = open(location, 'rb')
                msgImage = MIMEImage(fp.read())
                fp.close()
                msgImage.add_header('Content-ID', '<'+alias+'>')
                msg.attach(msgImage)

            try:
                msg.send()
            except Exception, e:
                logging.error("Couldn't send mail using the sendmail method: %s" % e)
    except Exception, e:
        logging.error('Email sending has failed: %s' % e)

    if is_invitate:
        exit(index)

def _send_mail_by_smtp(messages):
    if not settings.EMAIL_HOST:
        return

    if len(messages) == 0:
        return

    is_invitate=False
    sender = Header(unicode(settings.APP_SHORT_NAME), 'utf-8')
    sender.append('<%s>' % unicode(settings.DEFAULT_FROM_EMAIL))
    sender = u'%s <%s>' % (unicode(settings.APP_SHORT_NAME), unicode(settings.DEFAULT_FROM_EMAIL))

    try:
        index = 0
        connection = None
        for recipient, subject, html, text, media in messages:

            # we will reconnect the mail server for ever 100 mails
            if index % 90 == 0 :
                print "reconnect"
                connection = SMTP(str(settings.EMAIL_HOST), str(settings.EMAIL_PORT),
                                  local_hostname=DNS_NAME.get_fqdn(),timeout=50)

                if (bool(settings.EMAIL_USE_TLS)):
                    connection.ehlo()
                    connection.starttls()
                    connection.ehlo()

                if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD:
                    try:
                        if messages[0][0].type == "invitation":
                            is_invitate=True
                            connection.login("invitation1@stackpointer.info", str(settings.EMAIL_HOST_PASSWORD))
                    except AttributeError:
                        connection.login(str(settings.EMAIL_HOST_USER), str(settings.EMAIL_HOST_PASSWORD))

                if sender is None:
                    sender = str(settings.DEFAULT_FROM_EMAIL)


            msgRoot = MIMEMultipart('related')

            msgRoot['Subject'] = Header(subject, 'utf-8')
            msgRoot['From'] = sender

            to = Header(recipient.username, 'utf-8')
            to.append('<%s>' % recipient.email)
            print ">>>",recipient.email," ",index
            index += 1
            msgRoot['To'] = to

            msgRoot.preamble = 'This is a multi-part message from %s.' % unicode(settings.APP_SHORT_NAME).encode('utf8')

            msgAlternative = MIMEMultipart('alternative')
            msgRoot.attach(msgAlternative)

            msgAlternative.attach(MIMEText(text.encode('utf-8'), _charset='utf-8'))
            msgAlternative.attach(MIMEText(html.encode('utf-8'), 'html', _charset='utf-8'))

            for alias, location in media.items():
                fp = open(location, 'rb')
                msgImage = MIMEImage(fp.read())
                fp.close()
                msgImage.add_header('Content-ID', '<'+alias+'>')
                msgRoot.attach(msgImage)

            try:
                connection.sendmail(sender, [recipient.email], msgRoot.as_string())
                #send_mail("hello",msgRoot.as_string(),sender,[recipient.email],auth_user=str(settings.EMAIL_HOST_USER),auth_password=str(settings.EMAIL_HOST_PASSWORD))
            except Exception, e:
                logging.error("Couldn't send mail using the sendmail method: %s" % e)
                if e.smtp_error.startswith("5.4.5 Daily sending quota exceeded") and is_invitate:
                    exit(index-1)
                

        try:
            connection.quit()
        except socket.sslerror:
            connection.close()
    except Exception, e:
        logging.error('Email sending has failed: %s' % e)
    if is_invitate:
        exit(index)
