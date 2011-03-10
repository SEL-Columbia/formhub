"""
Testing POSTs to "/submission"
"""
from django.test import TestCase, Client

from xform_manager.models import Instance, XForm
from surveyor_manager.models import Surveyor
from datetime import datetime

PARSED_XFORMS_URL_ROOT = "/xforms"

import json

from xform_manager.factory import XFormManagerFactory
xfactory = XFormManagerFactory()

from parsed_xforms.models import xform_instances
from parsed_xforms import tag

import re

class TestFunctional(TestCase):
    def setUp(self):
        survey1 = xfactory.create_simple_instance({
            'geopoint': '40.765102558006795 -73.97389419555664 300.0 4.0'
        })
        survey2 = xfactory.create_simple_instance({
            'geopoint': '40.80937419746446 -73.95926006317139 300.0 4.0'
        })
    
    def test_map_data_is_accessible(self):
        c = Client()
        response = c.get("%s/data/map_data" % PARSED_XFORMS_URL_ROOT)
        self.assertEqual(response.status_code, 200)

        json_response = re.sub("Content-Type: text/html; charset=utf-8", "", str(response)).strip()
        j = json.loads(json_response)
        
        #assert that the factory-created survey shows up in the json
        #sent to the view
        self.assertTrue(len(j) > 0)