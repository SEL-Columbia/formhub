from datetime import datetime

from django.conf import settings
from django.test import TestCase, Client

from main.tests.test_base import MainTestCase

"""
Testing that data in parsed instance's mongo_dict is properly categorized.
"""
class TestMongoData(MainTestCase):
    def setUp(self):
        MainTestCase.setUp(self)
        self._publish_transportation_form_and_submit_instance()
        self.instances = settings.MONGO_DB.instances
        self.pi = self.xform.surveys.all()[0].parsed_instance

    def test_mongo_find_one(self):
        self.assertEquals(self.pi.to_dict(), self.instances.find_one())

    def test_mongo_find(self):
        self.assertEquals([self.pi.to_dict()], self.instances.find())

    def test_mongo_find_by_id(self):
        self.assertEquals(self.pi.to_dict(),
                self.instances.find_one({'id': self.pi.instance.id))
