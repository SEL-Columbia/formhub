from django.core.urlresolvers import reverse
from main.tests.test_base import MainTestCase
from odk_viewer.views import data_view

class TestDataView(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        self._create_user_and_login()
        self._publish_transportation_form_and_submit_instance()
        self.data_view_url = reverse(data_view, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })

    def test_data_view(self):
        response = self.client.get(self.data_view_url)
        self.assertEqual(response.status_code, 200)