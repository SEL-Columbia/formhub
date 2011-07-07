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
        sgs = list(CsvReader(os.path.join("data","table_definitions", "subgroups.csv")).iter_dicts())
        for sg in sgs:
            subgroups[sg['slug']] = sg['name']

        for name, slug in table_types:
            curtable = FacilityTable.objects.create(name=name, slug=slug)
            csv_reader = CsvReader(os.path.join("data","table_definitions", "%s.csv" % slug))
            display_order = 0
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
                try:
                    d = {
                        'name': input_d['name'],
                        'slug': input_d['slug'],
                        'subgroups': input_d['subgroups'],
                        'description': input_d.pop('description', ''),
                        'clickable': input_d.pop('clickable', 'no') == 'yes',
                        'click_action': input_d.pop('click action', input_d.pop('click_action', '')),
                        'display_style': input_d.pop('display style', input_d.pop('display_style', '')),
                        'calc_action': input_d.pop('calc action', input_d.pop('calc_action', '')),
                        'iconify_png_url': input_d.pop('iconify_png_url', input_d.pop('iconify png url', '')),
                        'calc_columns': input_d.pop('calc columns', input_d.pop('calc_columns', '')),
                        'display_order': display_order
                    }
                    display_order += 1
                    curtable.add_variable(d)
                except:
                    print "Error importing table definition for data: %s" % input_d
