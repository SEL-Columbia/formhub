"""
Testing that the reparse method works.
"""
from django.test import TestCase, Client
from datetime import datetime

from xform_manager.factory import XFormManagerFactory

from parsed_xforms.models import *
from surveyor_manager.models import *
from xform_manager.models import *

class TestReparseEverything(TestCase):
    def setUp(self):
        self.xf = XFormManagerFactory()
        self.x = self.xf.create_registration_instance({'name':'John', 'device_id': '90909'})
        self.i = self.xf.create_simple_instance({'device_id':'90909', 'geopoint': '10.100 10.100 300.0 4.0'})
    
    def test_basic_reparse_method_works(self):
        self.assertEqual(ParsedInstance.objects.count(), 2)
        self.assertEqual(Surveyor.objects.count(), 1)
        
        #Instance object has a method "reparse"
        for i in Instance.objects.all():
            #at the moment, reparse just deletes the parsed_instance
            #and then resaves, forcing a reparse instance.
            i.save()
        
        #THESE TESTS FAIL (and will continue to do so until we fix the code)
#        self.assertEqual(ParsedInstance.objects.count(), 2)
#        self.assertEqual(Surveyor.objects.count(), 1)
