#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import os, glob
from django.core.management.base import BaseCommand
from ... import models, utils

class Command(BaseCommand):
    help = "Import a folder of XForms for ODK."

    def handle(self, *args, **kwargs):
        path = args[0]
        for form in glob.glob( os.path.join(path, "*") ):
            form_parser = utils.FormParser(form)
            qs = models.Form.objects.filter(
                id_string=form_parser.get_id_string()
                )
            if qs.count()==0:
                xml_file = utils.django_file(
                    path=form,
                    field_name="xml_file",
                    content_type="text/xml"
                    )
                models.Form.objects.create(xml_file=xml_file, active=True)
