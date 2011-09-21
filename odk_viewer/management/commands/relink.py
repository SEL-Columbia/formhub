#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from django.core.management.base import BaseCommand
from ...models import Instance

class Command(BaseCommand):
    help = "Relink all instances with the current forms."

    def handle(self, *args, **kwargs):
        for instance in Instance.objects.all():
            instance._link()
            instance.save()
