# -*- coding: utf-8 -*-
from django.utils.html import strip_tags
from django.utils.translation import ugettext as _
from forum.models.action import ActionProxy
from forum.models import Comment, Question, Answer, NodeRevision,Tag
from forum.settings import THINGS_SUMMARY_LENGTH , REP_GAIN_BY_SUGGESTION
from django.utils.encoding import smart_unicode
from django.core.urlresolvers import reverse
import logging

class TagEditAction(ActionProxy):
    def create_revision_data(self,initial=False, **data):
        revision_data = dict(summary=data.get('summary', (initial and _('Initial revision') or '')))

        if data.get('title', None):
            revision_data['about'] = strip_tags(data['title'].strip())

        if data.get('text', None):
            revision_data['detail'] = data['text'].strip()

        return revision_data

    def target(self,viewer=None):
        tag_img = ""
        if self.tag.sponsor_tag_img:
            tag_img = '<img src="%s" height="16" width="18" alt class="sponsor-tag-img" >' % self.tag.sponsor_tag_img
            
        return '<a class="post-tag tag-link-%(tag_name)%" href="%(tag_url)s" rel="tag">%(tag_img)s%(tag_name)s</a>' % {
            'tag_name':smart_unicode(self.tag.name),
            'tag_url':reverse("tag_info",kwargs={'id':self.tag.id}),
            'tag_img':tag_img
            }

class TagReviseAction(TagEditAction):
    verb = _("edited")

    def process_data(self,**data):
        revision_data = self.create_revision_data(**data)
        revision = self.tag.create_revision(self.user, **revision_data)
        self.extra = revision.revision
        self.summary = revision.summary

    def process_action(self):
        self.tag.last_edited = self
        self.tag.save()

class TagSuggestAction(TagEditAction):
    verb = _("tag suggested")
    
    def process_data(self,**data):
        revision_data = self.create_revision_data(**data)
        revision = self.tag.create_suggestion(self.user, **revision_data)
        self.extra = revision.revision
        self.summary = revision.summary

    def process_action(self):
        self.tag.suggested = self
        self.tag.save()

class TagSuggestRejectAction(TagEditAction):
    def process_data(self, suggest=None):
        suggest.delete()

    def process_action(self):
        pass

class TagSuggestAcceptAction(TagEditAction):
    verb = _("accept suggestion")

    def repute_users(self):
        self.repute(self.tag.last_suggest.by, int(REP_GAIN_BY_SUGGESTION))

    def process_data(self, suggest=None):
        previous = self.tag.active_revision
        self.tag.activate_revision(self.user, suggest)
        self.extra = "%d:%d" % (previous.revision, suggest.revision)

    def process_action(self):
        self.tag.last_edited = self.tag.last_suggest
        self.tag.save()

