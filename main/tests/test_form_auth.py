from test_base import MainTestCase
from odk_logger.views import formList
from django.core.urlresolvers import reverse
from main.models import UserProfile
from main.views import login_redirect
import base64

class TestFormAuth(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        self._create_user_and_login('bob', 'bob')
        self._publish_transportation_form()
        self.url = reverse(formList, kwargs={'username': self.user.username})

    def _set_require_auth(self, auth=True):
        profile, created = UserProfile.objects.get_or_create(user=self.user)
        profile.require_auth = auth
        profile.save()

    def _set_auth_headers(self, username, password):
        return {
            'HTTP_AUTHORIZATION': 'Basic ' + base64.b64encode('%s:%s' % (username, password)),
        }

    def test_show_for_anon_when_require_auth_false(self):
        response = self.anon.get(self.url)
        self.assertEquals(response.status_code, 200)

    def test_show_for_user_when_require_auth_false(self):
        response = self.client.get(self.url)
        self.assertEquals(response.status_code, 200)

    def test_return_401_for_anon_when_require_auth_true(self):
        self._set_require_auth()
        response = self.anon.get(self.url)
        self.assertEquals(response.status_code, 401)

    def test_return_401_for_wrong_user_when_require_auth_true(self):
        self._set_require_auth()
        self._create_user_and_login('alice', 'alice')
        response = self.client.get(self.url)
        self.assertEquals(response.status_code, 401)
        response = self.client.get(self.url, **self._set_auth_headers('alice', 'alice'))
        self.assertEquals(response.status_code, 401)

    def test_show_for_user_when_require_auth_true(self):
        self._set_require_auth()
        response = self.client.get(self.url)
        self.assertEquals(response.status_code, 401)
        response = self.client.get(self.url, **self._set_auth_headers('bob', 'bob'))
        self.assertEquals(response.status_code, 200)

    def test_show_for_user_logged_out_when_require_auth_true(self):
        self._set_require_auth()
        response = self.anon.get(self.url)
        self.assertEquals(response.status_code, 401)
        response = self.anon.get(self.url, **self._set_auth_headers('bob', 'bob'))
        self.assertEquals(response.status_code, 200)

    def test_login_redirect_redirects(self):
        response = self.client.get(reverse(login_redirect))
        self.assertEquals(response.status_code, 302)
