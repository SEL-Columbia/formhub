#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from django.core.management.base import BaseCommand
from pyxform.xls2json import ExcelReader
from django.conf import settings
from nga_districts import models
import os

class Command(BaseCommand):
    help = "Load the LGAs from the Excel file into Django."

    MODEL_DICT = {
        u"Zones" : models.Zone,
        u"States" : models.State,
        u"LGAs" : models.LGA,
        u"zone" : models.Zone,
        u"state" : models.State,
        }

    ALLOWED_FIELDS = [u"id", u"name", u"scale_up"]

    def handle(self, *args, **kwargs):
        print """
        This is old code that should not be used. I wanted to hold
        onto it because there are some alternate spellings in LGAs.xls
        that might be useful. Instead you should call
        python manage.py loaddata nga_districts/fixtures/*.json
        """
        return

        path = os.path.join(settings.PROJECT_ROOT, "lga_hack", "LGAs.xls")
        excel_reader = ExcelReader(path)
        zones_states_lgas = excel_reader.to_dict()

        for sheet_name in [u"Zones", u"States", u"LGAs"]:
            for d in zones_states_lgas[sheet_name]:
                corresponding_model = self.MODEL_DICT[sheet_name]
                subset = {}
                for k, v in d.items():
                    if k in self.ALLOWED_FIELDS:
                        subset[k] = v
                    if k.endswith(u"_id"):
                        field_name = k[:len(k)-3]
                        cls = self.MODEL_DICT[field_name]
                        subset[field_name] = cls.objects.get(id=v)
                corresponding_model.objects.get_or_create(**subset)
