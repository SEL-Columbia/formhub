from django.core.management.base import BaseCommand
import os
import json
import time
import sys
from facilities.models import Facility, Variable, CalculatedVariable, \
    KeyRename, FacilityRecord
from facilities.facility_builder import FacilityBuilder
from utils.csv_reader import CsvReader
from django.conf import settings

from facility_views.models import *

class Command(BaseCommand):
    help = "Load the table defs from the csvs."

    def handle(self, *args, **kwargs):
        table_types = [
            ("Health", "health"),
            ("Education", "education"),
            ("Water", "water")
        ]
        FacilityTable.objects.all().delete()
        TableColumn.objects.all().delete()
        ColumnCategory.objects.all().delete()
        
        subgroups = {}
        sgs = list(CsvReader(os.path.join("facility_views","table_defs", "subgroups.csv")).iter_dicts())
        for sg in sgs:
            subgroups[sg['slug']] = sg['name']

        for name, slug in table_types:
            curtable = FacilityTable.objects.create(name=name, slug=slug)
            csv_reader = CsvReader(os.path.join("facility_views","table_defs", "%s.csv" % slug))
            for input_d in csv_reader.iter_dicts():
                subs = []
                for sg in input_d['subgroups'].split(" "):
                    if sg in subgroups:
                        subs.append({
                            'name': subgroups[sg],
                            'slug': sg
                        })
                for sub in subs:
                    curtable.add_column(sub)
                d = {
                    'name': input_d['name'],
                    'slug': input_d['slug'],
                    'subgroups': input_d['subgroups'],
                    'description': input_d.pop('description', ''),
                    'clickable': input_d.pop('clickable', 'no') == 'yes',
                    'click_action': input_d.pop('click action', input_d.pop('click_action', '')),
                }
                curtable.add_variable(d)
