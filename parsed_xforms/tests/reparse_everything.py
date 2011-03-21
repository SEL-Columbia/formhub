"""
Testing that the reparse method works.
"""
from django.test import TestCase, Client
from datetime import datetime

from xform_manager.factory import XFormManagerFactory

from parsed_xforms.models import *
from surveyor_manager.models import *

class TestReparseEverything(TestCase):
    def setUp(self):
        print "HERE"
        self.xf = XFormManagerFactory()
        self.xf.create_registration_instance({'name':'John', 'device_id': '90909'})
        self.xf.create_simple_instance({'device_id':'90909', 'geopoint': '10.100 10.100 300.0 4.0'})
    
    def tes_basic_reparse_method_works(self):
#        self.assertEqual(ParsedInstance.objects.count(), 1)
#        self.assertEqual(Surveyor.objects.count(), 1)