from django.core.management.base import BaseCommand
from django.core.management import call_command
#from django.db.models import Count
#import os
#import json
#import time
#import sys
#from collections import defaultdict
from facilities.models import Facility, Variable, CalculatedVariable, \
    KeyRename, FacilityRecord, Sector, LGAIndicator, GapVariable
#from nga_districts.models import LGA, LGARecord
#from facilities.facility_builder import FacilityBuilder
#from utils.csv_reader import CsvReader
#from django.conf import settings


class Command(BaseCommand):
    help = "Calculate the LGA indicators."

    def handle(self, *args, **kwargs):
        self.calculate_lga_indicators()
        self.calculate_lga_gaps()

    def calculate_lga_indicators(self):
        for i in LGAIndicator.objects.all():
            i.set_lga_values()

    def calculate_lga_gaps(self):
        for i in GapVariable.objects.all():
            i.set_lga_values()
