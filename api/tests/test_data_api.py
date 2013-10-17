from django.test import RequestFactory
from main.tests.test_base import MainTestCase

from api.views import DataViewSet, XFormViewSet


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
        view = DataViewSet.as_view({'get': 'list'})
        request = self.factory.get('/', **self.extra)
        response = view(request)
        self.assertEqual(response.status_code, 200)
        formid = self.xform.pk
        data = {
            u'transportation_2011_07_25':
            'http://testserver/api/v1/data/bob/%s' % formid
        }
        self.assertDictEqual(response.data, data)
        response = view(request, owner='bob', formid=formid)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertTrue(self.xform.surveys.count())
        dataid = self.xform.surveys.all()[0].pk

        data = {
            u'_bamboo_dataset_id': u'',
            u'_deleted_at': None,
            u'_attachments': [],
            u'_geolocation': [None, None],
            u'_xform_id_string': u'transportation_2011_07_25',
            u'transport/available_transportation_types_to_referral_facility':
            u'none',
            u'_status': u'submitted_via_web',
            u'_id': dataid
        }
        self.assertDictContainsSubset(data, response.data[0])
        response = view(request, owner='bob', formid=formid, dataid=dataid)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, dict)
        self.assertDictContainsSubset(data, response.data)

    def test_add_form_tag_propagates_to_data_tags(self):
        """Test that when a tag is applied on an xform,
        it propagates to the instance submissions
        """
        view = XFormViewSet.as_view({
            'get': 'labels',
            'post': 'labels',
            'delete': 'labels'
        })
        # no tags
        request = self.factory.get('/', **self.extra)
        response = view(request, owner='bob', pk=1, formid=1)
        self.assertEqual(response.data, [])
        # add tag "hello"
        request = self.factory.post('/', data={"tags": "hello"}, **self.extra)
        response = view(request, owner='bob', pk=1, formid=1)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, [u'hello'])
        for i in self.xform.surveys.all():
            self.assertIn(u'hello', i.tags.names())
        # remove tag "hello"
        request = self.factory.delete('/', data={"tags": "hello"},
                                      **self.extra)
        response = view(request, owner='bob', pk=1, formid=1, label='hello')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])
        for i in self.xform.surveys.all():
            self.assertNotIn(u'hello', i.tags.names())
