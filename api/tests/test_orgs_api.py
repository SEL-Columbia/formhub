import json

from api.tests.test_api import TestAPICase
from api.views import OrgProfileViewSet


class TestOrgsAPI(TestAPICase):
    def setUp(self):
        super(TestOrgsAPI, self).setUp()
        self.view = OrgProfileViewSet.as_view({
            'get': 'list',
            'post': 'create'
        })

    def test_orgs_list(self):
        self._org_create()
        request = self.factory.get('/', **self.extra)
        response = self.view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [self.company_data])

    def test_orgs_get(self):
        self._org_create()
        view = OrgProfileViewSet.as_view({
            'get': 'retrieve'
        })
        request = self.factory.get('/', **self.extra)
        response = view(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data, {'detail': 'Expected URL keyword argument `user`.'})
        request = self.factory.get('/', **self.extra)
        response = view(request, user='denoinc')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, self.company_data)

    def _org_create(self):
        request = self.factory.get('/', **self.extra)
        response = self.view(request)
        self.assertEqual(response.status_code, 200)
        data = {
            'org': u'denoinc',
            'name': u'Dennis',
            # 'email': u'info@deno.com',
            'city': u'Denoville',
            'country': u'US',
            #'organization': u'Dono Inc.',
            'home_page': u'deno.com',
            'twitter': u'denoinc',
            'description': u'',
            'address': u'',
            'phonenumber': u'',
            'require_auth': False,
            # 'password': 'denodeno',
        }
        # response = self.client.post(
        request = self.factory.post(
            '/api/v1/profiles', data=json.dumps(data),
            content_type="application/json", **self.extra)
        response = self.view(request)
        self.assertEqual(response.status_code, 201)
        data['url'] = 'http://testserver/api/v1/orgs/denoinc'
        data['user'] = 'http://testserver/api/v1/users/denoinc'
        data['creator'] = 'http://testserver/api/v1/users/bob'
        self.assertEqual(response.data, data)
        self.company_data = response.data

    def test_orgs_create(self):
        self._org_create()
