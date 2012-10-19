from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils import simplejson
import os
from main.tests.test_base import MainTestCase
from main.tests.test_form_api import dict_for_mongo_without_userform_id
from main.views import api
from odk_logger.models import XForm
from odk_viewer.models.parsed_instance import _encode_for_mongo


class TestParsedInstance(MainTestCase):
    def setUp(self):
        MainTestCase.setUp(self)
        self.instances = settings.MONGO_DB.instances
        self.instances.remove()
        xls_path = os.path.join(
            self.this_directory, 'fixtures',
            'userone',
            'userone_with_dot_name_fields.xls')
        count = XForm.objects.count()
        response = self._publish_xls_file(xls_path)
        self.assertEqual(XForm.objects.count(), count + 1)
        self.xform = XForm.objects.all().reverse()[0]
        self._make_submission(
            os.path.join(
                self.this_directory, 'fixtures',
                'userone',
                'userone_with_dot_name_fields' + '.xml'))
        self.pi = self.xform.surveys.all()[0].parsed_instance

    def test_apply_form_field_names(self):
        self.api_url = reverse(api, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })
        response = self.client.get(self.api_url, {})
        self.assertEqual(response.status_code, 200)
        d = dict_for_mongo_without_userform_id(
            self.xform.surveys.all()[0].parsed_instance)
        find_d = simplejson.loads(response.content)[0]
        find_d = map(_encode_for_mongo, sorted(find_d, key=find_d.get))
        self.assertEqual(find_d, sorted(d, key=d.get))
