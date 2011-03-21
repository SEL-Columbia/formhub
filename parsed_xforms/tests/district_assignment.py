"""
Test that districts are properly assigned to parsed_instances.
"""
from django.test import TestCase, Client
from datetime import datetime

import os
PATH_TO_FILE = os.path.realpath(__file__)
CURRENT_DIR = os.path.dirname(PATH_TO_FILE)
FIXTURES_DIR = os.path.join(CURRENT_DIR, "fixtures")

print "what the fizoo"
print FIXTURES_DIR

from parsed_xforms import models as px_models
from xform_manager import models as xm_models
from nga_districts.models import *

class TestDistrictLinkage(TestCase):
    """
    This tests something.
    """
    fixtures = ['lga.json']
    
    def test_xform_has_correct_fields(self):
        self.assertTrue(LGA.objects.count() > 0)
        xml = open(os.path.join(FIXTURES_DIR, "sample_southeast_ebonyi_izzi.xml")).read()
        expected_district = LGA.objects.get(unique_slug="ebonyi_izzi")
        i = xm_models.Instance(xml=xml)
        i.save()
        pi = px_models.ParsedInstance.objects.get(instance__id=i.id)
        
        self.assertTrue(pi.district != None)
        self.assertEquals(pi.district.name, expected_district.name)
