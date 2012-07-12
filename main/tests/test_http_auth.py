from django.core.urlresolvers import reverse
from django.test.client import Client
from main.tests.test_base import MainTestCase
from main import views

class TestBasicHttpAuthentication(MainTestCase):
    def setUp(self):
        self.client = Client()
        self._create_user_and_login(username='bob', password='bob')
        self._publish_transportation_form()
        self.api_url = reverse(views.api, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })
        self._logout()

    def test_http_auth(self):
        response = self.client.get(self.api_url)
        self.assertEqual(response.status_code, 401)
        # headers with invalid user/pass
        response = self.client.get(self.api_url,
                                    self._set_auth_headers('x', 'y'))
        self.assertEqual(response.status_code, 401)
        # headers with valid user/pass
        response = self.client.get(self.api_url,
            self._set_auth_headers('bob', 'bob'))
        self.assertEqual(response.status_code, 200)