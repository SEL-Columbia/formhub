"""
Test that districts are properly assigned to parsed_instances.
"""
from django.test import TestCase, Client
from datetime import datetime

import os
PATH_TO_FILE = os.path.realpath(__file__)
CURRENT_DIR = os.path.dirname(PATH_TO_FILE)
FIXTURES_DIR = os.path.join(CURRENT_DIR, "fixtures")

#print "what the fizoo"
#print FIXTURES_DIR

from parsed_xforms import models as px_models
from xform_manager import models as xm_models
from nga_districts.models import *

class TestDistrictLinkage(TestCase):
    """
    This tests something.
    """
    fixtures = ['lga.json', 'state.json']
    
    def setUp(self):
        self.fixture_xml = open(os.path.join(FIXTURES_DIR, "sample_southeast_ebonyi_izzi.xml")).read()
        self.expected_lga = LGA.objects.get(unique_slug="ebonyi_izzi")
    
    def test_a_district_gets_assigned_properly(self):
        self.assertTrue(LGA.objects.count() > 0)
        i = xm_models.Instance(xml=self.fixture_xml)
        i.save()
        pi = px_models.ParsedInstance.objects.get(instance__id=i.id)
        
        self.assertTrue(pi.lga != None)
        self.assertEquals(pi.lga.name, self.expected_lga.name)

    def test_district_gets_set_to_mongo(self):
        i = xm_models.Instance(xml=self.fixture_xml)
        i.save()
        
        pi = px_models.ParsedInstance.objects.get(instance__id=i.id)
        doc = pi.to_dict()
        
        #I assigned the 'matched_district/lga_id' in
        # the ParsedInstance update_mongo code
        mongo_lga_id = doc.get(u'matched_district/lga_id', None)
        
        self.assertEquals(mongo_lga_id, self.expected_lga.id)
