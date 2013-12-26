from django.db import models
from django.core.cache import cache
from django.utils.encoding import force_unicode
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.utils.translation import ugettext as _

from forum import settings

try:
    from cPickle import loads, dumps
except ImportError:
    from pickle import loads, dumps

from copy import deepcopy
from base64 import b64encode, b64decode
from zlib import compress, decompress
import re
import Image
import os

from base import BaseModel

MAX_MARKABLE_STRING_LENGTH = 100

class PickledObject(unicode):
    pass

def dbsafe_encode(value, compress_object=True):
    if not compress_object:
        value = b64encode(dumps(deepcopy(value)))
    else:
        value = b64encode(compress(dumps(deepcopy(value))))
    return PickledObject(value)

def dbsafe_decode(value, compress_object=True):
    if not compress_object:
        value = loads(b64decode(value))
    else:
        value = loads(decompress(b64decode(value)))
    return value

class PickledObjectField(models.Field):
    __metaclass__ = models.SubfieldBase

    marker_re = re.compile(r'^T\[(?P<type>\w+)\](?P<value>.*)$', re.DOTALL)
    markable_types = dict((t.__name__, t) for t in (str, int, unicode))

    def __init__(self, *args, **kwargs):
        self.compress = kwargs.pop('compress', True)
        self.protocol = kwargs.pop('protocol', 2)
        kwargs.setdefault('null', True)
        kwargs.setdefault('editable', False)
        super(PickledObjectField, self).__init__(*args, **kwargs)

    def generate_type_marked_value(self, value):
        return PickledObject(u"T[%s]%s" % (type(value).__name__, value))

    def read_marked_value(self, value):
        m = self.marker_re.match(value)

        if m:
            marker = m.group('type')
            value = m.group('value')
            if marker in self.markable_types:
                value = self.markable_types[marker](value)

        return value

    def get_default(self):
        if self.has_default():
            if callable(self.default):
                return self.default()
            return self.default

        return super(PickledObjectField, self).get_default()

    def to_python(self, value):
        if value is not None:
            try:
                if value.startswith("T["):
                    value = self.read_marked_value(value)
                else:
                    value = dbsafe_decode(value, self.compress)
            except:
                if isinstance(value, PickledObject):
                    raise
        return value

    def get_db_prep_value(self, value):
        if value is not None and not isinstance(value, PickledObject):
            if type(value).__name__ in self.markable_types and not (isinstance(value, basestring) and len(value
                                                                                                          ) > MAX_MARKABLE_STRING_LENGTH):
                value = unicode(self.generate_type_marked_value(value))
            else:
                value = unicode(dbsafe_encode(value, self.compress))
        return value

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)

    def get_internal_type(self):
        return 'TextField'

    def get_db_prep_lookup(self, lookup_type, value):
        if lookup_type not in ['exact', 'in', 'isnull']:
            raise TypeError('Lookup type %s is not supported.' % lookup_type)
        return super(PickledObjectField, self).get_db_prep_lookup(lookup_type, value)


class KeyValue(BaseModel):
    key = models.CharField(max_length=255, unique=True)
    value = PickledObjectField()

    class Meta:
        app_label = 'forum'

    def cache_key(self):
        return self._generate_cache_key(self.key)

    @classmethod
    def infer_cache_key(cls, querydict):
        try:
            key = [v for (k, v) in querydict.items() if k in ('key', 'key__exact')][0]

            return cls._generate_cache_key(key)
        except:
            return None

    @classmethod
    def value_to_list_on_cache_query(cls):
        return 'key'

def dimension_validator(image):
    """
    """
    if image.size > 1024:
        pass#todo

    if image.width > settings.GRAVATAR_MAX_WIDTH:
        raise ValidationError, _('Image width greater than allowed %spx') % settings.GRAVATAR_MAX_WIDTH

    if image.height > settings.GRAVATAR_MAX_HEIGHT:
        raise ValidationError, _('Image height greater than allowed %spx') % settings.GRAVATAR_MAX_HEIGHT

class Original(BaseModel):

    def upload_image(self, filename):
        return '%s/%s' % (settings.GRAVATAR_FOLDER, filename)

    image = models.ImageField(
        verbose_name = _('Original image'),
        upload_to    = upload_image,
        width_field  = 'image_width',
        height_field = 'image_height',
        validators   = [dimension_validator],
    )
    image_width = models.PositiveIntegerField(
        verbose_name = _('Image width'),
        editable = False,
        default = 0,
    )
    image_height = models.PositiveIntegerField(
        verbose_name = _('Image height'),
        editable = False,
        default = 0,
    )
    def __unicode__(self):
        return unicode(self.image)

    def get_absolute_url(self):
        return 'cropper_crop', [self.pk]    

    def get_image_url(self):
        return '%s%s' % (settings.GRAVATAR_ALIAS, os.path.basename(self.image.path))

    get_absolute_url = models.permalink(get_absolute_url)

    class Meta:
        app_label = 'forum'


class Cropped(BaseModel):
    def __unicode__(self):
        return u'%s-%sx%s' % (self.original, self.w, self.h)

    def upload_image(self, filename):
        return 'gravatar-%s' % (filename)

    def save(self, *args, **kwargs): #force_insert=False, force_update=False, using=None):
        source = self.original.image.path
        target = self.upload_image(os.path.basename(source))

        Image.open(source).crop([
            self.x,             # Left
            self.y,             # Top
            self.x + self.w,    # Right
            self.y + self.h     # Bottom
        ]).save(settings.GRAVATAR_FOLDER +"/"+ target)
        print settings.GRAVATAR_FOLDER +"/"+ target
        self.image = target        
        super(Cropped, self).save(*args, **kwargs)

    original = models.ForeignKey(Original,
        related_name = 'cropped',
        verbose_name = _('Original image'),
    )
    image = models.ImageField(
        verbose_name = _('Image'),
        upload_to    = upload_image,
        editable     = False,
    )
    x = models.PositiveIntegerField(
        verbose_name = _('Offset X'),
        default = 0,
    )
    y = models.PositiveIntegerField(
        verbose_name = _('Offset Y'),
        default = 0,
    )
    w = models.PositiveIntegerField(
        verbose_name = _('Cropped area width'),
        blank = True,
        null = True
    )
    h = models.PositiveIntegerField(
        verbose_name = _('Cropped area height'),
        blank = True,
        null = True
    )

    class Meta:
        app_label = 'forum'
        verbose_name = _('cropped image')
        verbose_name_plural = _('cropped images')
