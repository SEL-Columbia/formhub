#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from django.core.management.base import BaseCommand
from django.core.files.storage import get_storage_class
from odk_logger.models.attachment import Attachment
from utils.model_tools import queryset_iterator
from utils.logger_tools import get_dimensions, resize
from utils.viewer_tools import get_path

class Command(BaseCommand):
    help = "Creates thumbnails for all form images and stores them"

    def handle(self, *args, **kwargs):
        for att in queryset_iterator(Attachment.objects.all()):
            filename = att.media_file.name
            default_storage = get_storage_class()()
            if not default_storage.exists(get_path(filename, '-med.')):
                try:
                    resize(filename)
                    print 'Thumbnail created for %s' % filename
                except Exception, e:
                    print 'Error on %s: %s' % (filename, e.message)
