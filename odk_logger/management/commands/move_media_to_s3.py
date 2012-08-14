#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from django.core.management.base import BaseCommand
from django.core.files.storage import get_storage_class
from odk_logger.models.attachment import Attachment
from odk_logger.models.attachment import upload_to as attachment_upload_to
from odk_logger.models.xform import XForm
from odk_logger.models.xform import upload_to as xform_upload_to
import sys
from django.utils.translation import ugettext as _, ugettext_lazy


class Command(BaseCommand):
    help = ugettext_lazy("Moves all attachments and xls files "
                         "to s3 from the local file system storage.")

    def handle(self, *args, **kwargs):
        try:
            fs = get_storage_class('django.core.files.storage.FileSystemStorage')()
            s3 = get_storage_class('storages.backends.s3boto.S3BotoStorage')()
        except:
            print _(u"Missing necessary libraries. Try running: pip install -r requirements-s3.pip")
            sys.exit(1)

        default_storage = get_storage_class()()
        if default_storage.__class__ != s3.__class__:
            print _(u"You must first set your default storage to s3 in your local_settings.py file.")
            sys.exit(1)

        classes_to_move = [
            (Attachment, 'media_file', attachment_upload_to),
            (XForm, 'xls', xform_upload_to),
        ]

        for cls, file_field, upload_to in classes_to_move:
            print _("Moving %(class)ss to s3...") % {'class': cls.__name__}
            for i in cls.objects.all():
                f = getattr(i, file_field)
                old_filename = f.name
                if f.name and fs.exists(f.name) and not s3.exists(upload_to(i, f.name)):
                    f.save(fs.path(f.name), fs.open(fs.path(f.name)))
                    print (_("\t+ '%(fname)s'\n\t---> '%(url)s'") 
                           % {'fname': fs.path(old_filename), 'url': f.url})
                else:
                    print "\t- (f.name=%s, fs.exists(f.name)=%s, not s3.exists(upload_to(i, f.name))=%s)" \
                        % (f.name, fs.exists(f.name), not s3.exists(upload_to(i, f.name)))
