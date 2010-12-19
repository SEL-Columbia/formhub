#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import os, glob
from django.core.management.base import BaseCommand
from django.core.files.uploadedfile import InMemoryUploadedFile
from ...models import make_submission, InstanceImage

def django_file(path, field_name, content_type):
    # adapted from here: http://groups.google.com/group/django-users/browse_thread/thread/834f988876ff3c45/
    f = open(path)
    return InMemoryUploadedFile(
        file=f,
        field_name=field_name,
        name=f.name,
        content_type=content_type,
        size=os.path.getsize(path),
        charset=None
        )

class Command(BaseCommand):
    help = "Import a folder of ODK instances."

    def handle(self, *args, **kwargs):
        path = args[0]
        for instance in glob.glob( os.path.join(path, "*") ):
            xml_files = glob.glob( os.path.join(instance, "*.xml") )
            if len(xml_files)<1: continue
            # if len(xml_files)>1: raise Exception(
            #     "Figure out how to handle multiple XML files",
            #     xml_files
            #     )
            if len(xml_files)>1: print xml_files
            f = django_file(xml_files[0],
                            field_name="xml_file",
                            content_type="text/xml")
            s = make_submission(f)

            for jpg in glob.glob( os.path.join(instance, "*.jpg") ):
                f = django_file(jpg,
                                field_name="image",
                                content_type="image/jpeg")
                InstanceImage.objects.get_or_create(
                    instance=s.instance, image=f
                    )
