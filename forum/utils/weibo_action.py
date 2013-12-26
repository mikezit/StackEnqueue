from weibo import Client as weibo_client
from forum.models import User
from forum.models import AuthKeyUserAssociation, ValidationHash, Question, Answer
from forum import settings
import urlparse

def weibo_get(user,method):
    try:
        assoc = AuthKeyUserAssociation.objects.filter(provider="weibo").get(user=user)
    except AuthKeyUserAssociation.DoesNotExist:
        return None

    token={}
    token["access_token"]=assoc.key
    token["uid"]=assoc.weibo_uid
    token["remind_in"]=assoc.weibo_remind_in
    token["expires_at"]=int(assoc.weibo_expires_at)
    client = weibo_client(str(settings.WEIBO_API_KEY), str(settings.WEIBO_API_SECRET),urlparse.urljoin(settings.APP_URL,'/weibo/signin/check'),token)
    return client.get(method, uid=token["uid"])

def weibo_post(user,status):
    try:
        assoc = AuthKeyUserAssociation.objects.filter(provider="weibo").get(user=user)
    except AuthKeyUserAssociation.DoesNotExist:
        return # the user is not registed by weibo

    token={}
    token["access_token"]=assoc.key
    token["uid"]=assoc.weibo_uid
    token["remind_in"]=assoc.weibo_remind_in
    token["expires_at"]=int(assoc.weibo_expires_at)
    client = weibo_client(str(settings.WEIBO_API_KEY), str(settings.WEIBO_API_SECRET),urlparse.urljoin(settings.APP_URL,'/weibo/signin/check'),token)
    client.post('statuses/update', status=status)
