from api.tests.test_api import TestAPICase
from api.views import XFormViewSet


class TestFormsAPI(TestAPICase):
    def setUp(self):
        super(TestFormsAPI, self).setUp()
        self.view = XFormViewSet.as_view({
            'get': 'list',
        })

    def test_form_list(self):
        self._publish_xls_form_to_project()
        request = self.factory.get('/', **self.extra)
        response = self.view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [self.form_data])

    def test_form_get(self):
        self._publish_xls_form_to_project()
        view = XFormViewSet.as_view({
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
        self.assertEqual(response.data, self.form_data)
