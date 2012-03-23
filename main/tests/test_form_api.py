from django.core.urlresolvers import reverse
from django.utils import simplejson

from test_base import MainTestCase
from main.views import api
from odk_viewer.models.parsed_instance import dict_for_mongo

class TestFormAPI(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        self._create_user_and_login()
        self._publish_transportation_form_and_submit_instance()
        self.api_url = reverse(api, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })

    def test_api(self):
        # query string
        response = self.client.get(self.api_url, {})
        self.assertEqual(response.status_code, 200)
        d = dict_for_mongo(
                self.xform.surveys.all()[0].parsed_instance.to_dict())
        find_d = simplejson.loads(response.content)[0]
        self.assertEqual(sorted(find_d, key=find_d.get), sorted(d, key=d.get))

    def test_api_with_query(self):
        # query string
        data = {
            'transport/available_transportation_types_to_referral_facility':\
                'none'
        }
        response = self.client.get(self.api_url, data)
        self.assertEqual(response.status_code, 200)
        d = dict_for_mongo(
                self.xform.surveys.all()[0].parsed_instance.to_dict())
        find_d = simplejson.loads(response.content)[0]
        self.assertEqual(sorted(find_d, key=find_d.get), sorted(d, key=d.get))

    def test_api_query_no_records(self):
        # query string
        data = {
            'available_transporation_types_to_referral_facility':\
                'bicycle'
        }
        response = self.client.get(self.api_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '[]')
