#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from django.core.management.base import BaseCommand
from django.core.files.storage import get_storage_class
from django.conf import settings
from odk_logger.models.attachment import Attachment
from utils.model_tools import queryset_iterator
from utils.logger_tools import get_dimensions, resize, resize_local_env, \
                                write_exif
from utils.viewer_tools import get_path
from utils.geotag import set_gps_location

class Command(BaseCommand):
    help = "Creates thumbnails for all form images and stores them"

    def handle(self, *args, **kwargs):
        fs = get_storage_class('django.core.files.storage.FileSystemStorage')()
        for att in queryset_iterator(Attachment.objects.select_related('instance', 'instance__xform').all()):
            filename = att.media_file.name
            default_storage = get_storage_class()()
            if not default_storage.exists(get_path(filename, 
                                    settings.THUMB_CONF['small']['suffix'])):
                write_exif(att)
                try:
                    if default_storage.__class__ != fs.__class__:
                        resize(filename)
                    else:
                        resize_local_env(filename)
                    if default_storage.exists(get_path(filename, 
                                    settings.THUMB_CONF['small']['suffix'])):
                        print 'Thumbnails created for %s' % filename
                    else:
                        print 'Something didn\'t go right for %s' % filename
                except (IOError, OSError), e:
                    print 'Error on %s: %s' % (filename, e)
