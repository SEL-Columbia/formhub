"""
Testing that the reparse method works.
"""
from django.test import TestCase, Client
from datetime import datetime

from odk_logger.factory import XFormManagerFactory

from odk_viewer.models import *
from odk_logger.models import *


class TestReparseEverything(TestCase):
    def setUp(self):
        self.xf = XFormManagerFactory()
        self.x = self.xf.create_registration_instance({u'name':u'John', u'device_id': u'90909'})
        self.i = self.xf.create_simple_instance({u'device_id':u'90909', u'geopoint': u'10.100 10.100 300.0 4.0'})

    def test_basic_reparse_method_works(self):
        self.assertEqual(ParsedInstance.objects.count(), 2)

        for i in Instance.objects.all():
            i.save()

        self.assertEqual(ParsedInstance.objects.count(), 2)
