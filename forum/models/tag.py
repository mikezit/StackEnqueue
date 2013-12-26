import datetime
from base import *

from django.utils.translation import ugettext as _
from django.utils.encoding import smart_unicode, force_unicode

from forum import modules

class ActiveTagManager(CachedManager):
    use_for_related_fields = True

    def get_query_set(self):
        return super(ActiveTagManager, self).get_query_set().exclude(used_count__lt=1)

class TagContent(models.Model):
    about      = models.CharField(max_length=300,null=True,default="")
    detail     = models.TextField(null=True,default="")
    author     = models.ForeignKey(User, related_name='%(class)ss',null=True)

    class Meta:
        abstract = True
        app_label = 'forum'

class Tag(BaseModel,TagContent):
    name       = models.CharField(max_length=255, unique=True)
    pinyin     = models.CharField(max_length=255,default="")
    created_by      = models.ForeignKey(User, related_name='created_tags')
    created_at      = models.DateTimeField(default=datetime.datetime.now, blank=True, null=True)
    sponsor_tag_img = models.URLField(max_length=200, blank=True)
    marked_by       = models.ManyToManyField(User, related_name="marked_tags", through="MarkedTag")
    active_revision = models.OneToOneField('TagRevision', related_name='active', null=True)
    last_edited     = models.ForeignKey('Action', null=True, unique=True, related_name="edited_tag")
    suggested        = models.ForeignKey('Action', null=True, unique=True, related_name="suggest_tag")

    # Denormalised data
    used_count = models.PositiveIntegerField(default=0)
    view_times =  models.PositiveIntegerField(default=0)
    active = ActiveTagManager()

    class Meta:
        ordering = ('-used_count', 'name')
        app_label = 'forum'

    def __unicode__(self):
        return force_unicode(self.name)

    def add_to_usage_count(self, value):
        if self.used_count + value < 0:
            self.used_count = 0
        else:
            self.used_count = models.F('used_count') + value

    def cache_key(self):
        return self._generate_cache_key(Tag.safe_cache_name(self.name))

    @classmethod
    def safe_cache_name(cls, name):
        return "".join([str(ord(c)) for c in name])

    @classmethod
    def infer_cache_key(cls, querydict):
        if 'name' in querydict:
            return cls._generate_cache_key(cls.safe_cache_name(querydict['name']))

        return None

    @classmethod
    def value_to_list_on_cache_query(cls):
        return 'name'

    @models.permalink
    def get_absolute_url(self):
        return ('tag_questions', (), {'tag': self.name})

    def _create_revision(self, user, number,suggested=False, **kwargs):
        revision = TagRevision(author=user, revision=number,tag=self,suggested=suggested, **kwargs)

        if suggested:
            revision.suggest_status = "pendding"

        revision.save()
        return revision

    def create_suggestion(self,user,**kwargs):
        cur_num = self.revisions.aggregate(last=models.Max('revision'))['last']
        number = 1
        if cur_num is not None:
            number =  cur_num + 1

        #check if there is pendding suggestion create the user
        if not self.pendding_suggestion :
            suggestion = self._create_revision(user, number,True, **kwargs)
        elif user == self.pendding_suggestion.author: # update suggestion
            suggestion = self.pendding_suggestion
            suggestion.about = kwargs["about"]
            suggestion.summary = kwargs["summary"]
            if "detail" in kwargs.keys():
                suggestion.detail = kwargs["detail"]
            suggestion.save()
        else:
            return None
            
        return suggestion

    def create_revision(self,user,**kwargs):
        cur_num = self.revisions.aggregate(last=models.Max('revision'))['last']
        number = 1
        if cur_num is not None:
            number =  cur_num + 1
        revision = self._create_revision(user, number, **kwargs)
        self.activate_revision(user, revision)
        return revision
        

    def activate_revision(self, user, revision):
        self.about = revision.about
        self.detail = revision.detail
        
        self.active_revision = revision

        print "in activate_revision"
        if revision.suggested:
            print "change status"
            revision.suggest_status = "accepted"

        revision.save()
        self.save()

    @property
    def last_suggest(self):
        return self.suggested

    @property
    def pendding_suggestion(self):
        s_tag = self.revisions.filter(suggested=True).order_by('-revised_at')

        if len(s_tag) is 0:
            return None

        rev = s_tag[0]
        if rev.suggest_status != "pendding":
            return None

        return rev

    def save(self, *args, **kwargs):
        if not self.id:
            super(BaseModel, self).save(*args, **kwargs)
            self.active_revision = self._create_revision(self.author, 1,about=self.about,detail=self.detail)
            self.activate_revision(self.author, self.active_revision)

        super(Tag, self).save(*args, **kwargs)
                                                         

class MarkedTag(models.Model):
    TAG_MARK_REASONS = (('good', _('interesting')), ('bad', _('ignored')),('none', _('none')))
    tag = models.ForeignKey(Tag, related_name='user_selections')
    user = models.ForeignKey(User, related_name='tag_selections')
    reason = models.CharField(max_length=16, choices=TAG_MARK_REASONS,default="none")
    subscribed = models.BooleanField(default=False)

    class Meta:
        app_label = 'forum'


class TagRevision(BaseModel,TagContent):
    tag        = models.ForeignKey(Tag, related_name='revisions')
    summary    = models.CharField(max_length=300)
    revision   = models.PositiveIntegerField()
    revised_at = models.DateTimeField(default=datetime.datetime.now)
    suggested  = models.BooleanField(default=False)
    suggest_status = models.CharField(max_length=16,default="")

    class Meta:
        unique_together = ('tag', 'revision')
        app_label = 'forum'
