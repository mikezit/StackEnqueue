# -*- coding: utf-8 -*-
import time
import os
import posixpath
import datetime
import math
import re
import logging
import random
import operator
from django import template
from django.utils.encoding import smart_unicode, force_unicode, smart_str
from django.utils.safestring import mark_safe
from django.utils import dateformat
from forum.models import Question, Answer, QuestionRevision, AnswerRevision, NodeRevision,Tag
from django.utils.translation import ugettext as _
from django.utils.translation import ungettext
from django.utils import simplejson
from forum import settings
from django.template.defaulttags import url as default_url
from forum import skins
from forum.utils import html
from extra_filters import decorated_int
from django.core.urlresolvers import reverse
from django.db.models import Q


register = template.Library()

LOCAL_GRAVATAR_TEMPLATE = ('<img class="gravatar" width="%(size)s" height="%(size)s" '
'src="%(gravatar)s" '
'alt="%(username)s\'s gravatar image" />')

GRAVATAR_TEMPLATE = ('<img class="gravatar" width="%(size)s" height="%(size)s" '
'src="http://www.gravatar.com/avatar/%(gravatar_hash)s'
'?s=%(size)s&amp;d=%(default)s&amp;r=%(rating)s" '
'alt="%(username)s\'s gravatar image" />')

@register.simple_tag
def weibo_gravatar(user,size):
    try:
        image_url = user.weibo_gravatar
        username = user.username
        return mark_safe(LOCAL_GRAVATAR_TEMPLATE % {
                'size': size,
                'gravatar': image_url,
                'username': template.defaultfilters.urlencode(username),
                })
    except (TypeError, AttributeError, KeyError):
        return real_gravatar(user,size)        

@register.simple_tag
def local_gravatar(user,size):
    try:
        image = user.local_gravatar
        image_url = "%s%s" % (settings.GRAVATAR_ALIAS,image)
        username = user.username
        return mark_safe(LOCAL_GRAVATAR_TEMPLATE % {
                'size': size,
                'gravatar': image_url,
                'username': template.defaultfilters.urlencode(username),
                })
    except (TypeError, AttributeError, KeyError):
        return real_gravatar(user,size)        

@register.simple_tag
def gravatar(user,size):
    try:
        if user.use_weibo_gravatar:
            return weibo_gravatar(user,size)
        elif user.use_local_gravatar:
            return local_gravatar(user,size)
        else:
            return real_gravatar(user,size)
    except (TypeError, AttributeError, KeyError):
        return real_gravatar(user,size)        

@register.simple_tag
def real_gravatar(user, size):
    try:
        gravatar = user['gravatar']
        username = user['username']
    except (TypeError, AttributeError, KeyError):
        gravatar = ""
        username = ""
        if user is not None:
            gravatar = user.gravatar
            username = user.username
    return mark_safe(GRAVATAR_TEMPLATE % {
    'size': size,
    'gravatar_hash': gravatar,
    'default': settings.GRAVATAR_DEFAULT_IMAGE,
    'rating': settings.GRAVATAR_ALLOWED_RATING,
    'username': template.defaultfilters.urlencode(username),
    })

@register.simple_tag
def get_tags(user):
    #if user.is_suspended():
    #    return _("(suspended)")

    TAGS_NUM=5
    TAG_TEMPLATE = '<a href="/tags/%s">%s</a>'
    marktags = user.tag_selections.filter(Q(subscribed=True)|Q(reason='good'))

    tags = []
    for marktag in marktags:
        try:
            tags.append(marktag.tag.name)
        except Tag.DoesNotExist:
            pass

    if len(tags) < TAGS_NUM:
        #first we find user's qustions and answers
        nodes = user.nodes.filter(Q(node_type="question")|Q(node_type="answer")).order_by("-added_at")
        for node in nodes[:10]:
            if node.node_type == "answer":
                node = node.parent
            tags += [tag.name for tag in node.tags.all()]

        #sort the tag by used times
        tags_set = set(tags)
        tags_num = {}
        for tag in tags_set:
            tags_num[tag]=tags.count(tag)
        sorted_tags = sorted(tags_num.iteritems(), key=operator.itemgetter(1),reverse=True)
        
        tags = [tag for tag,num in sorted_tags ]
            
    html = ""
    try:
        for i in range(len(tags[:TAGS_NUM])):
            if i != 0:
                html += ","
            html += TAG_TEMPLATE % (tags[i],tags[i]) 
    except UnicodeDecodeError:
        pass

    html = smart_unicode(html, encoding='utf-8', strings_only=False, errors='strict')
    return mark_safe(html)

@register.simple_tag
def tags_html(tags):
    TAGS_TEMPLATE='<a class="post-tag">%(tag)s</a>'
    html = ""
    for tag in tags:
        html += TAGS_TEMPLATE % {"tag":tag}
    html = smart_unicode(html, encoding='utf-8', strings_only=False, errors='strict')
    return mark_safe(html)
    
@register.simple_tag
def get_reputation(user):
    if user.is_suspended():
        return _("(suspended)")

    repstr = decorated_int(user.reputation, "")
    BADGE_TEMPLATE = '<span class="reputation-score" title="%(reputation)s %(reputationword)s">%(repstr)s</span>'
    BADGE_TEMPLATE = smart_unicode(BADGE_TEMPLATE, encoding='utf-8', strings_only=False, errors='strict')
    return mark_safe(BADGE_TEMPLATE % {
    'reputation' : user.reputation,
    'repstr': repstr,
    'reputationword' : _('reputation'),
    })


@register.simple_tag
def get_location(user):
    #if user.is_suspended():
    #    return _("(suspended)")

    location = user.location;
    LOCATION_TEMPLATE = '<span class="location" >%(location)s</span>'
    LOCATION_TEMPLATE = smart_unicode(LOCATION_TEMPLATE, encoding='utf-8', strings_only=False, errors='strict')
    return mark_safe( LOCATION_TEMPLATE % {
            'location':location
            })
    

@register.simple_tag
def get_score_badge(user):
    #if user.is_suspended():
    #    return _("(suspended)")

    repstr = decorated_int(user.reputation, "")

    BADGE_TEMPLATE = ''
    if user.gold > 0 :
        BADGE_TEMPLATE = '%s%s' % (BADGE_TEMPLATE, '<span  title="%(gold)s %(badgesword)s">'
        '<span class="gold">&#9679;</span>'
        '<span class="badgecount">%(gold)s</span>'
        '</span>')
    if user.silver > 0:
        BADGE_TEMPLATE = '%s%s' % (BADGE_TEMPLATE, '<span  title="%(silver)s %(badgesword)s">'
        '<span class="silver">&#9679;</span>'
        '<span class="badgecount">%(silver)s</span>'
        '</span>')
    if user.bronze > 0:
        BADGE_TEMPLATE = '%s%s' % (BADGE_TEMPLATE, '<span  title="%(bronze)s %(badgesword)s">'
        '<span class="bronze">&#9679;</span>'
        '<span class="badgecount">%(bronze)s</span>'
        '</span>')
    BADGE_TEMPLATE = smart_unicode(BADGE_TEMPLATE, encoding='utf-8', strings_only=False, errors='strict')
    return mark_safe(BADGE_TEMPLATE % {
    'gold' : user.gold,
    'silver' : user.silver,
    'bronze' : user.bronze,
    'badgesword' : _('badges'),
    })

# Usage: {% get_accept_rate node.author %}
@register.simple_tag
def get_accept_rate(user):
    # We get the number of all user's answers.
    total_answers_count = Answer.objects.filter(author=user).count()

    # We get the number of the user's accepted answers.
    accepted_answers_count = Answer.objects.filter(author=user, state_string__contains="(accepted)").count()

    # In order to represent the accept rate in percentages we divide the number of the accepted answers to the
    # total answers count and make a hundred multiplication.
    try:
        accept_rate = (float(accepted_answers_count) / float(total_answers_count) * 100)
    except ZeroDivisionError:
        accept_rate = 0

    # If the user has more than one accepted answers the rate title will be in plural.
    if accepted_answers_count > 1:
        accept_rate_number_title = _('%(user)s has %(count)d accepted answers') % {
            'user' :  smart_unicode(user.username),
            'count' : int(accepted_answers_count)
        }
    # If the user has one accepted answer we'll be using singular.
    elif accepted_answers_count == 1:
        accept_rate_number_title = _('%s has one accepted answer') % smart_unicode(user.username)
    # This are the only options. Otherwise there are no accepted answers at all.
    else:
        accept_rate_number_title = _('%s has no accepted answers') % smart_unicode(user.username)

    html_output = """
<span class="accept_rate warm" title="%(accept_rate_label)s%(accept_rate)d&#37">
      %(accept_rate)d&#37
</span>
    """ % {
        'accept_rate_label' : _('accept rate'),
        'accept_rate_title' : _('Rate of the user\'s accepted answers'),
        'accept_rate' : int(accept_rate),
        'accept_rate_number_title' : u'%s' % accept_rate_number_title,
    }

    return mark_safe(html_output)

# Usage: {% get_accept_rate node.author %}
@register.simple_tag
def get_accept_rate2(user):
    # We get the number of all user's answers.
    total_answers_count = Answer.objects.filter(author=user).count()

    # We get the number of the user's accepted answers.
    accepted_answers_count = Answer.objects.filter(author=user, state_string__contains="(accepted)").count()

    # In order to represent the accept rate in percentages we divide the number of the accepted answers to the
    # total answers count and make a hundred multiplication.
    try:
        accept_rate = (float(accepted_answers_count) / float(total_answers_count) * 100)
    except ZeroDivisionError:
        accept_rate = 0

    # If the user has more than one accepted answers the rate title will be in plural.
    if accepted_answers_count > 1:
        accept_rate_number_title = _('%(user)s has %(count)d accepted answers') % {
            'user' :  smart_unicode(user.username),
            'count' : int(accepted_answers_count)
        }
    # If the user has one accepted answer we'll be using singular.
    elif accepted_answers_count == 1:
        accept_rate_number_title = _('%s has one accepted answer') % smart_unicode(user.username)
    # This are the only options. Otherwise there are no accepted answers at all.
    else:
        accept_rate_number_title = _('%s has no accepted answers') % smart_unicode(user.username)

    html_output = """
    <span class="accept_rate" title=%(accept_rate_number_title)s">%(accept_rate)d&#37;</span>
    """ % {
        'accept_rate_title' : _('Rate of the user\'s accepted answers'),
        'accept_rate' : int(accept_rate),
        'accept_rate_number_title' : u'%s' % accept_rate_number_title,
    }

    return mark_safe(html_output)

@register.simple_tag
def get_age(birthday):
    current_time = datetime.datetime(*time.localtime()[0:6])
    year = birthday.year
    month = birthday.month
    day = birthday.day
    diff = current_time - datetime.datetime(year, month, day, 0, 0, 0)
    return diff.days / 365

@register.simple_tag
def join_date(date, limen=2):
    if not date:
        return _('unknown')
    
    now = datetime.datetime.now()
    diff = now - date
    months = diff.days/30
    years = diff.days/365
    days = diff.days
    hours = int(diff.seconds/3600)
    minutes = int(diff.seconds/60)

    if months < 12 :#less than one year
        if days > 30:
            return ungettext('%(mon)d ' + _("month ago"), '%(mon)d ' + _("months ago"), months) % {'mon':months}
        elif days >=2:
            return ungettext('%(day)d ' + _("day ago"), '%(day)d ' + _("days ago"), months) % {'day':days}
        elif days == 2:
            return _('2 days ago')
        elif days == 1:
            return _('yesterday')
        elif minutes >= 60:
            return ungettext('%(hr)d ' + _("hour ago"), '%(hr)d ' + _("hours ago"), hours) % {'hr':hours}
        elif diff.seconds >= 60:
            return ungettext('%(min)d ' + _("min ago"), '%(min)d ' + _("mins ago"), minutes) % {'min':minutes}
        else:
            return ungettext('%(sec)d ' + _("sec ago"), '%(sec)d ' + _("secs ago"), diff.seconds) % {'sec':diff.seconds}
    else:
        return ungettext('%(yr)d'+ _("year")+' %(mon)d ' + _("month ago"), '%(yr)d ' + _("year")+ '%(mon)d ' + _("months ago"), months) % {'mon':months%12,'yr':years}

    
@register.simple_tag
def diff_date(date, limen=2):
    if not date:
        return _('unknown')

    now = datetime.datetime.now()
    diff = now - date
    days = diff.days
    hours = int(diff.seconds/3600)
    minutes = int(diff.seconds/60)

    if days > 2:
        if date.year == now.year:
            return _("%(month)s %(day)s,%(hour)s:%(minute)s") % {'month':date.month,'day':date.day,'hour':date.hour,'minute':date.minute}
        else: #cross year
            return _("%(year)s %(month)s %(day)s,%(hour)s:%(minute)s") % {'year':date.year-2000,'month':date.month,'day':date.day,'hour':date.hour,'minute':date.minute}

    elif days == 2:
        return _('2 days ago')
    elif days == 1:
        return _('yesterday')
    elif minutes >= 60:
        return ungettext('%(hr)d ' + _("hour ago"), '%(hr)d ' + _("hours ago"), hours) % {'hr':hours}
    elif diff.seconds >= 60:
        return ungettext('%(min)d ' + _("min ago"), '%(min)d ' + _("mins ago"), minutes) % {'min':minutes}
    else:
        return ungettext('%(sec)d ' + _("sec ago"), '%(sec)d ' + _("secs ago"), diff.seconds) % {'sec':diff.seconds}

@register.simple_tag
def media(url):
    url = skins.find_media_source(url)
    if url:
        # Create the URL prefix.
        url_prefix = settings.STATIC_PATH + '/m/'

        # Make sure any duplicate forward slashes are replaced with a single
        # forward slash.
        if not url_prefix.startswith("http://"):
            url_prefix = re.sub("/+", "/", url_prefix)

        url = url_prefix + url
        return url

class ItemSeparatorNode(template.Node):
    def __init__(self, separator):
        sep = separator.strip()
        if sep[0] == sep[-1] and sep[0] in ('\'', '"'):
            sep = sep[1:-1]
        else:
            raise template.TemplateSyntaxError('separator in joinitems tag must be quoted')
        self.content = sep

    def render(self, context):
        return self.content

class BlockMediaUrlNode(template.Node):
    def __init__(self, nodelist):
        self.items = nodelist

    def render(self, context):
        prefix = settings.APP_URL + 'm/'
        url = ''
        if self.items:
            url += '/'
        for item in self.items:
            url += item.render(context)

        url = skins.find_media_source(url)
        url = prefix + url
        out = url
        return out.replace(' ', '')

@register.tag(name='blockmedia')
def blockmedia(parser, token):
    try:
        tagname = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("blockmedia tag does not use arguments")
    nodelist = []
    while True:
        nodelist.append(parser.parse(('endblockmedia')))
        next = parser.next_token()
        if next.contents == 'endblockmedia':
            break
    return BlockMediaUrlNode(nodelist)


@register.simple_tag
def fullmedia(url):
    domain = settings.APP_BASE_URL
    #protocol = getattr(settings, "PROTOCOL", "http")
    path = media(url)
    return "%s%s" % (domain, path)


class SimpleVarNode(template.Node):
    def __init__(self, name, value):
        self.name = name
        self.value = template.Variable(value)

    def render(self, context):
        context[self.name] = self.value.resolve(context)
        return ''

class BlockVarNode(template.Node):
    def __init__(self, name, block):
        self.name = name
        self.block = block

    def render(self, context):
        source = self.block.render(context)
        context[self.name] = source.strip()
        return ''


@register.tag(name='var')
def do_var(parser, token):
    tokens = token.split_contents()[1:]

    if not len(tokens) or not re.match('^\w+$', tokens[0]):
        raise template.TemplateSyntaxError("Expected variable name")

    if len(tokens) == 1:
        nodelist = parser.parse(('endvar',))
        parser.delete_first_token()
        return BlockVarNode(tokens[0], nodelist)
    elif len(tokens) == 3:
        return SimpleVarNode(tokens[0], tokens[2])

    raise template.TemplateSyntaxError("Invalid number of arguments")

class DeclareNode(template.Node):
    dec_re = re.compile('^\s*(\w+)\s*(:?=)\s*(.*)$')

    def __init__(self, block):
        self.block = block

    def render(self, context):
        source = self.block.render(context)

        for line in source.splitlines():
            m = self.dec_re.search(line)
            if m:
                clist = list(context)
                clist.reverse()
                d = {}
                d['_'] = _
                d['os'] = os
                d['html'] = html
                d['reverse'] = reverse
                d['smart_str'] = smart_str
                d['smart_unicode'] = smart_unicode
                d['force_unicode'] = force_unicode
                for c in clist:
                    d.update(c)
                try:
                    command = m.group(3).strip()
                    context[m.group(1).strip()] = eval(command, d)
                except Exception, e:
                    logging.error("Error in declare tag, when evaluating: %s" % m.group(3).strip())
                    raise
        return ''

@register.tag(name='declare')
def do_declare(parser, token):
    nodelist = parser.parse(('enddeclare',))
    parser.delete_first_token()
    return DeclareNode(nodelist)

# Usage: {% random 1 999 %}
# Generates random number in the template
class RandomNumberNode(template.Node):
    # We get the limiting numbers
    def __init__(self, int_from, int_to):
        self.int_from = int(int_from)
        self.int_to = int(int_to)

    # We generate the random number using the standard python interface
    def render(self, context):
        return str(random.randint(self.int_from, self.int_to))

@register.tag(name="random")
def random_number(parser, token):
    # Try to get the limiting numbers from the token
    try:
        tag_name, int_from, int_to = token.split_contents()
    except ValueError:
        # If we had no success -- raise an exception
        raise template.TemplateSyntaxError, "%r tag requires exactly two arguments" % token.contents.split()[0]

    # Call the random Node
    return RandomNumberNode(int_from, int_to)
