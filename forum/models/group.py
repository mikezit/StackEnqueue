from base import *
from utils import PickledObjectField
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Group as DjangoGroup
from django.db.models import Q
from django.utils.encoding import smart_unicode
import string
from random import Random

class Group(BaseModel,DjangoGroup):
    pass

    
