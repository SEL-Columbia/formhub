#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from django.core.management.base import BaseCommand
from odk_dashboard import models
from odk_dropbox.models import Instance

class Command(BaseCommand):
    help = "Delete and recreate all parsed instances."

    def handle(self, *args, **kwargs):
        models.ParsedInstance.objects.all().delete()
        print "Reparsings all instances"
        for i in Instance.objects.all():
            models.parse(i)
