from django.core.urlresolvers import reverse
from django.utils import simplejson

from test_base import MainTestCase
from main.views import api
from odk_viewer.models.parsed_instance import ParsedInstance, \
    _encode_for_mongo, _decode_from_mongo
import base64

def dict_for_mongo_without_userform_id(parsed_instance):
    d = parsed_instance.to_dict_for_mongo()
    # remove _userform_id since its not returned by the API
    d.pop(ParsedInstance.USERFORM_ID)
    return d

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
        d = dict_for_mongo_without_userform_id(
            self.xform.surveys.all()[0].parsed_instance)
        find_d = simplejson.loads(response.content)[0]
        self.assertEqual(sorted(find_d, key=find_d.get), sorted(d, key=d.get))

    def test_api_with_query(self):
        # query string
        json = '{"transport/available_transportation_types_to_referral_facility":"none"}'
        data = {'query': json}
        response = self.client.get(self.api_url, data)
        self.assertEqual(response.status_code, 200)
        d = dict_for_mongo_without_userform_id(self.xform.surveys.all()[0].parsed_instance)
        find_d = simplejson.loads(response.content)[0]
        self.assertEqual(sorted(find_d, key=find_d.get), sorted(d, key=d.get))

    def test_api_query_no_records(self):
        # query string
        json = '{"available_transporation_types_to_referral_facility": "bicycle"}'
        data = {'query': json}
        response = self.client.get(self.api_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '[]')

    def test_handle_bad_json(self):
        response = self.client.get(self.api_url, {'query': 'bad'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(True, 'JSON' in response.content)

    def test_api_jsonp(self):
        # query string
        callback = 'jsonpCallback'
        response = self.client.get(self.api_url, {'callback': callback})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.startswith(callback + '('), True)
        self.assertEqual(response.content.endswith(')'), True)
        start = callback.__len__() + 1
        end = response.content.__len__() - 1
        content = response.content[start: end]
        d = dict_for_mongo_without_userform_id(self.xform.surveys.all()[0].parsed_instance)
        find_d = simplejson.loads(content)[0]
        self.assertEqual(sorted(find_d, key=find_d.get), sorted(d, key=d.get))

    def test_api_with_query_start_limit(self):
        # query string
        json = '{"transport/available_transportation_types_to_referral_facility":"none"}'
        data = {'query': json, 'start': 0, 'limit': 10}
        response = self.client.get(self.api_url, data)
        self.assertEqual(response.status_code, 200)
        d = dict_for_mongo_without_userform_id(self.xform.surveys.all()[0].parsed_instance)
        find_d = simplejson.loads(response.content)[0]
        self.assertEqual(sorted(find_d, key=find_d.get), sorted(d, key=d.get))

    def test_api_with_query_invalid_start_limit(self):
        # query string
        json = '{"transport/available_transportation_types_to_referral_facility":"none"}'
        data = {'query': json, 'start': -100, 'limit': -100}
        response = self.client.get(self.api_url, data)
        self.assertEqual(response.status_code, 400)

    def test_api_count(self):
        # query string
        json = '{"transport/available_transportation_types_to_referral_facility":"none"}'
        data = {'query': json, 'count': 1}
        response = self.client.get(self.api_url, data)
        self.assertEqual(response.status_code, 200)
        find_d = simplejson.loads(response.content)[0]
        self.assertTrue(find_d.has_key('count'))
        self.assertEqual(find_d.get('count'), 1)

    def test_api_column_select(self):
        # query string
        json = '{"transport/available_transportation_types_to_referral_facility":"none"}'
        columns = '["transport/available_transportation_types_to_referral_facility"]'
        data = {'query': json, 'fields': columns}
        response = self.client.get(self.api_url, data)
        self.assertEqual(response.status_code, 200)
        find_d = simplejson.loads(response.content)[0]
        self.assertTrue(find_d.has_key('transport/available_transportation_types_to_referral_facility'))
        self.assertFalse(find_d.has_key('_attachments'))

    def test_api_decode_from_mongo(self):
        field = "$section1.group01.question1"
        encoded = _encode_for_mongo(field)
        self.assertEqual(encoded, ("%(dollar)ssection1%(dot)sgroup01%(dot)squestion1" % \
                                   {"dollar": base64.b64encode("$"), \
                                    "dot": base64.b64encode(".")}))
        decoded = _decode_from_mongo(encoded)
        self.assertEqual(field, decoded)

    def test_api_with_or_query(self):
        """Test that an or query is interpreted correctly since we use an
        internal or query to filter out deleted records"""
        for i in range(1, 3):
            self._submit_transport_instance(i)
        #record 0: does NOT have the 'transport/loop_over_transport_types_frequency/ambulance/frequency_to_referral_facility' field
        #record 1 'transport/loop_over_transport_types_frequency/ambulance/frequency_to_referral_facility': 'daily'
        #record 2 'transport/loop_over_transport_types_frequency/ambulance/frequency_to_referral_facility': 'weekly'
        params = {
            'query':
                '{"$or": [{"transport/loop_over_transport_types_frequency/ambulance/frequency_to_referral_facility": "weekly"}, '
                '{"transport/loop_over_transport_types_frequency/ambulance/frequency_to_referral_facility": "daily"}]}'}
        response = self.client.get(self.api_url, params)
        self.assertEqual(response.status_code, 200)
        data = simplejson.loads(response.content)
        self.assertEqual(len(data), 2)

        # check that blank params give us all our records i.e. 3
        params = {}
        response = self.client.get(self.api_url, params)
        self.assertEqual(response.status_code, 200)
        data = simplejson.loads(response.content)
        self.assertEqual(len(data), 3)
