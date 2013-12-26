# -*- coding: utf-8 -*-
from django.core.management.base import NoArgsCommand
from forum.models import Tag
from forum.utils.pinyin import get_pinyin


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        tags = Tag.objects.all()
        for tag in tags:
            tag.pinyin = get_pinyin(unicode(tag.name, "utf-8"))
            tag.save()
