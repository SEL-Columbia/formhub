#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import os, glob
from django.core.management.base import BaseCommand
from django.utils.translation import ugettext_lazy
from ... import models
import utils.viewer_tools

class Command(BaseCommand):
    help = ugettext_lazy("Import a folder of XForms for ODK.")

    def handle(self, *args, **kwargs):
        path = args[0]
        for form in glob.glob( os.path.join(path, "*") ):
            f = open(form)
            models.XForm.objects.get_or_create(xml=f.read(), active=False)
            f.close()
