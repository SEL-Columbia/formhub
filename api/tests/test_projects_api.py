import json

from api.tests.test_api import TestAPICase
from api.views import ProjectViewSet


class TestProjectsAPI(TestAPICase):
    def setUp(self):
        super(TestProjectsAPI, self).setUp()
        self.view = ProjectViewSet.as_view({
            'get': 'list',
            'post': 'create'
        })

    def test_projects_list(self):
        self._project_create()
        request = self.factory.get('/', **self.extra)
        response = self.view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [self.project_data])

    def test_projects_get(self):
        self._project_create()
        view = ProjectViewSet.as_view({
            'get': 'retrieve'
        })
        request = self.factory.get('/', **self.extra)
        response = view(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data,
                         {'detail': 'Expected URL keyword argument `owner`.'})
        request = self.factory.get('/', **self.extra)
        response = view(request, owner='bob', pk=1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, self.project_data)

    def _project_create(self):
        data = {
            'name': u'demo',
            'owner': 'http://testserver/api/v1/users/bob'
        }
        request = self.factory.post(
            '/', data=json.dumps(data),
            content_type="application/json", **self.extra)
        response = self.view(request, owner='bob')
        self.assertEqual(response.status_code, 201)
        data['url'] = 'http://testserver/api/v1/projects/bob/%s' % 1
        self.assertDictContainsSubset(data, response.data)
        self.project_data = response.data

    def test_projects_create(self):
        self._project_create()
