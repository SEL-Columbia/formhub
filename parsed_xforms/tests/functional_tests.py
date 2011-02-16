"""
Testing POSTs to "/submission"
"""
from django.test import TestCase, Client

from xform_manager.models import Instance, XForm
from surveyor_manager.models import Surveyor
from datetime import datetime

PARSED_XFORMS_URL_ROOT = "/xforms"

class TestFunctional(TestCase):

    def test_map_data_is_accessible(self):
        c = Client()
        
        response = c.get("%s/data/map_data" % PARSED_XFORMS_URL_ROOT)
        self.assertEqual(response.status_code, 200)
