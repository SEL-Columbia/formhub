#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from django.core.management.base import BaseCommand
from django.utils.translation import ugettext_lazy
from odk_viewer.reparse import *

class Command(BaseCommand):
    help = ugettext_lazy("Delete and recreate parsed instances.")

    def handle(self, *args, **kwargs):
        reparse_all(debug=True)
