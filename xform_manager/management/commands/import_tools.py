#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import os, glob
from django.core.management.base import BaseCommand
from django.core.management import call_command

from xform_manager.import_tools import import_instances_from_jonathan
from xform_manager.models import Instance, XForm

#in case we want to monitor these model counts--
# from parsed_xforms.models import ParsedInstance, Registration
# from nga_districts import models as nga_models
# from surveyor_manager.models import Surveyor

from django.contrib.auth.models import User
from django.conf import settings

xform_db = settings.MONGO_DB
xform_instances = xform_db.instances

IMAGES_DIR = os.path.join(settings.MEDIA_ROOT, "attachments")

class Command(BaseCommand):
    help = "Import ODK forms and instances."

    def handle(self, *args, **kwargs):
        path = args[0]
        print "[Importing XForm Instances from %s]\n" % path
        im_count = len(glob.glob(os.path.join(IMAGES_DIR, '*')))
        instance_count = Instance.objects.count()
        print "Before Parse:"
        print " --> Images:    %d" % im_count
        print " --> Instances: %d" % Instance.objects.count()
        
        import_instances_from_jonathan(path)
        
        im_count2 = len(glob.glob(os.path.join(IMAGES_DIR, '*')))
        print "After Parse:"
        print " --> Images:    %d" % im_count2
        print " --> Instances: %d" % Instance.objects.count()
#        print glob.glob(os.path.join(path, "*"))
