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
        if len(args) > 0:
            self._data_dir = args[0]
        else:
            self._data_dir = "data"
        table_types = [
            ("Health", "health"),
            ("Education", "education"),
            ("Water", "water")
        ]
        self.delete_existing_values()
        self.load_subgroups()
        self.load_table_types(table_types)
        self.load_layer_descriptions()

    def load_layer_descriptions(self):
        layer_descriptions = list(CsvReader(os.path.join(self._data_dir,"map_layers", "layer_details.csv")).iter_dicts())
        for layer in layer_descriptions:
            MapLayerDescription.objects.get_or_create(**layer)

    def delete_existing_values(self):
        FacilityTable.objects.all().delete()
        TableColumn.objects.all().delete()
        ColumnCategory.objects.all().delete()

    def load_subgroups(self):
        self.subgroups = {}
        sgs = list(CsvReader(os.path.join(self._data_dir,"table_definitions", "subgroups.csv")).iter_dicts())
        for sg in sgs:
            self.subgroups[sg['slug']] = sg['name']

    def load_table_types(self, table_types):
        for name, slug in table_types:
            curtable = FacilityTable.objects.create(name=name, slug=slug)
            csv_reader = CsvReader(os.path.join(self._data_dir,"table_definitions", "%s.csv" % slug))
            display_order = 0
            for input_d in csv_reader.iter_dicts():
                subs = []
                for sg in input_d['subgroups'].split(" "):
                    if sg in self.subgroups:
                        subs.append({
                            'name': self.subgroups[sg],
                            'slug': sg
                        })
                for sub in subs:
                    curtable.add_column(sub)
                try:
                    input_d['display_order'] = display_order
                    d = TableColumn.load_row_from_csv(input_d)
                    display_order += 1
                    curtable.add_variable(d)
                except:
                    print "Error importing table definition for data: %s" % input_d
