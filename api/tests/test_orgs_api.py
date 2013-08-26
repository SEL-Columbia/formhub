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

    def test_orgs_create(self):
        self._org_create()
