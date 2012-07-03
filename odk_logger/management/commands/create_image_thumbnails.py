#!/usr/bin/env python

from django.core.management.base import BaseCommand
from django.core.files.storage import get_storage_class
from django.conf import settings

from odk_logger.models.attachment import Attachment
from utils.image_tools import get_dimensions, resize, resize_local_env
from utils.model_tools import queryset_iterator
from utils.viewer_tools import get_path
from django.utils.translations import ugext_lazy as _

class Command(BaseCommand):
    help = "Creates thumbnails for all form images and stores them"

    def handle(self, *args, **kwargs):
        fs = get_storage_class('django.core.files.storage.FileSystemStorage')()
        for att in queryset_iterator(Attachment.objects.select_related(
                    'instance', 'instance__xform').all()):
            filename = att.media_file.name
            default_storage = get_storage_class()()
            if not default_storage.exists(get_path(filename,
                                    settings.THUMB_CONF['smaller']['suffix'])):
                try:
                    if default_storage.__class__ != fs.__class__:
                        resize(filename)
                    else:
                        resize_local_env(filename)
                    if default_storage.exists(get_path(filename,
                                    settings.THUMB_CONF['smaller']['suffix'])):
                        print _(u'Thumbnails created for %s') % filename
                    else:
                        print _(u'Something didn\'t go right for %s') % filename
                except (IOError, OSError, ZeroDivisionError), e:
                    print _(u'Error on %s: %s') % (filename, e)
