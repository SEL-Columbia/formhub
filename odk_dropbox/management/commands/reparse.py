#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from django.core.management.base import BaseCommand
from ...models import xform_instances, Instance

class Command(BaseCommand):
    help = "Delete and recreate parsed instances."

    def handle(self, *args, **kwargs):
        xform_instances.remove()
        for i in Instance.objects.all():
            print "*"
            i.save_to_mongo()
