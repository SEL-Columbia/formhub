#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import os, glob
from django.core.management.base import BaseCommand
from django.core.files.uploadedfile import InMemoryUploadedFile
from ... import models, utils

class Command(BaseCommand):
    help = "Import a folder of ODK instances."

    def handle(self, *args, **kwargs):
        path = args[0]
        for instance in glob.glob( os.path.join(path, "*") ):
            xml_files = glob.glob( os.path.join(instance, "*.xml") )
            if len(xml_files)<1: continue
            # we need to figure out what to do if there are multiple
            # xml files in the same folder.
            xml_file = utils.django_file(xml_files[0],
                                         field_name="xml_file",
                                         content_type="text/xml")
            images = []
            for jpg in glob.glob(os.path.join(instance, "*.jpg")):
                images.append(
                    utils.django_file(jpg,
                                      field_name="image",
                                      content_type="image/jpeg")
                    )
            try:
                models.get_or_create_instance(xml_file, images)
            except utils.MyError, e:
                print e

            # close the files
            xml_file.close()
            for i in images: i.close()
