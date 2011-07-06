from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from facilities.models import Facility
import csv
import os

class Command(BaseCommand):
    help = "Export the facilities into .csv files."

    def handle(self, *args, **kwargs):
        for sector, facilities in Facility.export_geocoords().iteritems():
            with open(os.path.join('export', '%s.csv' % sector), 'wb') as _file:
                writer = csv.writer(_file)
                for facility in facilities:
                    writer.writerow([facility['id'], facility['lat'], facility['long']])
