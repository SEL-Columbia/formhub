from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from django.core.management import call_command

from xform_manager.models import Instance, XForm
#from surveyor_manager.models import Surveyor
from datetime import datetime

PARSED_XFORMS_URL_ROOT = "/xforms"

import json

from xform_manager.factory import XFormManagerFactory
xfactory = XFormManagerFactory()

from parsed_xforms.models import xform_instances, ParsedInstance
from parsed_xforms.views import map_data_points
from nga_districts.models import Zone, State, LGA
import common_tags as tag

import re

class TestFunctional(TestCase):
    def setUp(self):
        self.zone_slug = 'southeast'
        self.state_slug = 'anambra'
        self.lga_slug = 'awka_north'
        self.zone, created = Zone.objects.get_or_create(
            name="Southeast", slug="southeast")
        self.state, created = State.objects.get_or_create(
            zone=self.zone, name="Anambra", slug="anambra")
        self.lga, created = LGA.objects.get_or_create(
            state=self.state, name="Awka North", slug=self.lga_slug)

        # THIS WILL NOT WORK FOR TESTING BECAUSE CREATING A SIMPLE
        # INSTANCE THROUGH XFORM_MANAGER.FACTORY WILL NOT ALLOW FOR
        # ZONE STATE AND LGA FIELDS, THESE ARE NECESSARY TO TEST THE
        # CURRENT MAP VIEW AS IT HAS BEEN BROKEN UP BY LGA
        self.survey1 = xfactory.create_simple_instance({
            'geopoint': '40.765102558006795 -73.97389419555664 300.0 4.0',
            'zone' : self.zone_slug,
            'state_in_southeast' : self.state_slug,
            'lga_in_anambra': self.lga_slug,
        })
        print self.survey1.xml
        self.survey2 = xfactory.create_simple_instance({
            'geopoint': '40.80937419746446 -73.95926006317139 300.0 4.0',
            'zone' : self.zone_slug,
            'state_in_southeast' : self.state_slug,
            'lga_in_anambra': self.lga_slug,
        })

    def test_there_two_parsed_instances_with_lga_set_correctly(self):
        self.assertEqual(ParsedInstance.objects.all().count(), 2)
        for pi in ParsedInstance.objects.all():
            self.assertEqual(pi.lga, self.lga)
    
    def test_map_data_is_accessible(self):
        url = reverse(map_data_points, kwargs={'lga_id' : self.lga.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
    
        json_response = re.sub("Content-Type: text/html; charset=utf-8", "", str(response)).strip()
        j = json.loads(json_response)
        
        #assert that the factory-created survey shows up in the json
        #sent to the view
        self.assertTrue(len(j) > 0)
