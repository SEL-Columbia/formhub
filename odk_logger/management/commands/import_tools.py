#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import os, glob
from django.core.management.base import BaseCommand
from django.core.management import call_command

from odk_logger.import_tools import import_instances_from_zip
from odk_logger.models import Instance, XForm

from django.contrib.auth.models import User
from django.conf import settings
from django.utils.translation import ugettext_lazy as _


IMAGES_DIR = os.path.join(settings.MEDIA_ROOT, "attachments")


class Command(BaseCommand):
    help = "Import ODK forms and instances."

    def handle(self, *args, **kwargs):
        path = args[0]
        debug = False
        if debug:
            print _(u"[Importing XForm Instances from %s]\n") % path
            im_count = len(glob.glob(os.path.join(IMAGES_DIR, '*')))
            instance_count = Instance.objects.count()
            print _(u"Before Parse:")
            print _(u" --> Images:    %d") % im_count
            print _(u" --> Instances: %d") % Instance.objects.count()
        import_instances_from_zip(path)
        if debug:
            im_count2 = len(glob.glob(os.path.join(IMAGES_DIR, '*')))
            print _(u"After Parse:")
            print _(u" --> Images:    %d") % im_count2
            print _(u" --> Instances: %d") % Instance.objects.count()
