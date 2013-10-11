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
        response = view(request, owner='bob', pk=self.project.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, self.project_data)

    def test_projects_create(self):
        self._project_create()

    def test_publish_xls_form_to_project(self):
        self._publish_xls_form_to_project()

    def test_view_xls_form(self):
        self._publish_xls_form_to_project()
        view = ProjectViewSet.as_view({
            'get': 'forms'
        })
        request = self.factory.get('/', **self.extra)
        response = view(request, owner='bob', pk=self.project.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [self.form_data])
        response = view(request, owner='bob',
                        pk=self.project.pk, formid=self.xform.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, self.form_data)
