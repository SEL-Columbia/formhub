#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import os, glob
from django.core.management.base import BaseCommand
from django.core.management import call_command

from odk_logger.import_tools import import_instances_from_jonathan
from odk_logger.models import Instance, XForm

from django.contrib.auth.models import User
from django.conf import settings


IMAGES_DIR = os.path.join(settings.MEDIA_ROOT, "attachments")


class Command(BaseCommand):
    help = "Import ODK forms and instances."

    def handle(self, *args, **kwargs):
        path = args[0]
        debug = False
        if debug:
            print "[Importing XForm Instances from %s]\n" % path
            im_count = len(glob.glob(os.path.join(IMAGES_DIR, '*')))
            instance_count = Instance.objects.count()
            print "Before Parse:"
            print " --> Images:    %d" % im_count
            print " --> Instances: %d" % Instance.objects.count()
        import_instances_from_jonathan(path)
        if debug:
            im_count2 = len(glob.glob(os.path.join(IMAGES_DIR, '*')))
            print "After Parse:"
            print " --> Images:    %d" % im_count2
            print " --> Instances: %d" % Instance.objects.count()
