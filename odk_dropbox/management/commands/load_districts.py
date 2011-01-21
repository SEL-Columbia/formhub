#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from django.core.management.base import BaseCommand
from odk_dashboard.models import GPS, District

class Command(BaseCommand):
    help = "A hard link to the districts' fixture file."
    
    def handle(self, *args, **kwargs):
		call_command('loaddata', 'odk_dashboard/districts/district.json')