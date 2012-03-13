from datetime import datetime

from django.conf import settings
from django.test import TestCase, Client

import common_tags
from main.tests.test_base import MainTestCase

"""
Testing that data in parsed instance's mongo_dict is properly categorized.
"""
class TestMongoData(MainTestCase):
    def setUp(self):
        MainTestCase.setUp(self)
        self.instances = settings.MONGO_DB.instances
        self.instances.remove()
        self.assertEquals(list(self.instances.find()), [])
        self._publish_transportation_form_and_submit_instance()
        self.pi = self.xform.surveys.all()[0].parsed_instance

    def test_mongo_find_one(self):
        self.assertEquals(self.pi.to_dict(), self.instances.find_one())

    def test_mongo_find(self):
        self.assertEquals([self.pi.to_dict()], list(self.instances.find()))

    def test_mongo_find_by_id(self):
        self.assertEquals(self.pi.to_dict(), self.instances.find_one(
                    {common_tags.ID: self.pi.instance.id}))

    def test_mongo_find_by_uuid(self):
        self.assertEquals(self.pi.to_dict(), self.instances.find_one(
                    {common_tags.UUID: self.pi.instance.uuid}))

    def test_mongo_find_by_key_value_pair(self):
        for key, value in self.pi.to_dict().items():
            self.assertEquals(self.pi.to_dict(), self.instances.find_one(
                        {key: value}))
