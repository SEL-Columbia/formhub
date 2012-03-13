from datetime import datetime
import os

from django.conf import settings
from django.test import TestCase, Client

import common_tags
from main.tests.test_base import MainTestCase
from odk_logger.models import XForm

'''
Testing that data in parsed instance's mongo_dict is properly categorized.
'''
class TestMongoData(MainTestCase):
    def setUp(self):
        MainTestCase.setUp(self)
        self.instances = settings.MONGO_DB.instances
        self.instances.remove()
        self.assertEquals(list(self.instances.find()), [])
        xls_path = os.path.join(self.this_directory, 'fixtures',
                'transportation', 'mongo',
                'transportation_with_dirty_mongo_ids.xls')
        count = XForm.objects.count()
        response = self._publish_xls_file(xls_path)
        self.assertEqual(XForm.objects.count(), count + 1)
        self.xform = XForm.objects.all().reverse()[0]
        self._make_submission(os.path.join(self.this_directory, 'fixtures',
                    'transportation', 'mongo',
                    'transport_2011-07-25_19-05-36' + '.xml'))
        self.pi = self.xform.surveys.all()[0].parsed_instance

    def test_mongo_find_one(self):
        self.assertEquals(self.pi.to_dict_for_mongo(),
                self.instances.find_one())

    def test_mongo_find(self):
        self.assertNotEquals([self.pi.to_dict()], list(self.instances.find()))
        self.assertEquals([self.pi.to_dict_for_mongo()],
                list(self.instances.find()))

    def test_mongo_find_by_id(self):
        self.assertEquals(self.pi.to_dict_for_mongo(), self.instances.find_one(
                    {common_tags.ID: self.pi.instance.id}))

    def test_mongo_find_by_uuid(self):
        self.assertEquals(self.pi.to_dict_for_mongo(), self.instances.find_one(
                    {common_tags.UUID: self.pi.instance.uuid}))

    def test_mongo_find_by_key_value_pair(self):
        for key, value in self.pi.to_dict_for_mongo().items():
            self.assertEquals(self.pi.to_dict_for_mongo(),
                    self.instances.find_one({key: value}))
