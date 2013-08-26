from django.test import RequestFactory
from main.tests.test_base import MainTestCase

from api.views import DataList


class TestDataAPI(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        self._create_user_and_login()
        self._publish_transportation_form()
        self._make_submissions()
        self.factory = RequestFactory()
        self.extra = {
            'HTTP_AUTHORIZATION': 'Token %s' % self.user.auth_token}

    def test_form_list(self):
        view = DataList.as_view()
        request = self.factory.get('/', **self.extra)
        response = view(request)
        self.assertEqual(response.status_code, 200)
        data = {
            u'transportation_2011_07_25': 'http://testserver/api/v1/data/bob/1'
        }
        self.assertDictEqual(response.data, data)
        response = view(request, owner='bob', formid=1)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        data = {
            u'_bamboo_dataset_id': u'',
            u'_deleted_at': None,
            u'_attachments': [],
            u'_geolocation': [None, None],
            u'_xform_id_string': u'transportation_2011_07_25',
            u'transport/available_transportation_types_to_referral_facility':
            u'none',
            u'_status': u'submitted_via_web',
            u'_id': 1
        }
        self.assertDictContainsSubset(data, response.data[0])
        response = view(request, owner='bob', formid=1, dataid=1)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, dict)
        self.assertDictContainsSubset(data, response.data)
