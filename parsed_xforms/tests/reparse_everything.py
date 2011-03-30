"""
Testing that the reparse method works.
"""
from django.test import TestCase, Client
from datetime import datetime

from xform_manager.factory import XFormManagerFactory

from parsed_xforms.models import *
from surveyor_manager.models import *
from xform_manager.models import *

from django.conf import settings
xform_instances = settings.MONGO_DB.instances

class TestReparseEverything(TestCase):
    def setUp(self):
        self.xf = XFormManagerFactory()
        self.x = self.xf.create_registration_instance({'name':'John', 'device_id': '90909'})
        self.i = self.xf.create_simple_instance({'device_id':'90909', 'geopoint': '10.100 10.100 300.0 4.0'})
    
    def test_basic_reparse_method_works(self):
        self.assertEqual(ParsedInstance.objects.count(), 2)
        self.assertEqual(xform_instances.count(), 2)
        self.assertEqual(Surveyor.objects.count(), 1)
        
        for i in Instance.objects.all():
            i.save()

        self.assertEqual(ParsedInstance.objects.count(), 2)
        self.assertEqual(xform_instances.count(), 2)
        self.assertEqual(Surveyor.objects.count(), 1)
