#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from django.core.management.base import BaseCommand
from odk_dashboard.models import GPS, District

class Command(BaseCommand):
    help = "Iterates through GPS objects and assigns a district ID based on the 'latlng_string' column of district."
    
    def handle(self, *args, **kwargs):
        district_count = District.objects.count()
        if district_count==0:
            print "You need to load the district data from the fixtures before running this script. (or run 'manage.py load_districts')"
        else:
            gpss = GPS.objects.all()
            for g in gpss:
               g.district = g.closest_district()
               g.save()
