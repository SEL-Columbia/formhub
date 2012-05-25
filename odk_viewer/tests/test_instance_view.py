from django.core.urlresolvers import reverse
from main.tests.test_base import MainTestCase
from odk_viewer.views import instance

class TestInstanceView(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        self._create_user_and_login()
        self._publish_transportation_form_and_submit_instance()
        self.instance_view_url = reverse(instance, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })

    def test_instance_view(self):
        response = self.client.get(self.instance_view_url)
        self.assertEqual(response.status_code, 200)