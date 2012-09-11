from test_base import MainTestCase
from odk_logger.views import enter_data
from django.core.urlresolvers import reverse
from odk_logger.models import XForm
from main.views import set_perm, show
from main.models import MetaData
from django.conf import settings
from urlparse import urlparse

class TestFormEnterData(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        self._create_user_and_login()
        self._publish_transportation_form_and_submit_instance()
        self.perm_url = reverse(set_perm, kwargs={
            'username': self.user.username, 'id_string': self.xform.id_string})
        self.show_url = reverse(show,
                    kwargs={'uuid': self.xform.uuid})
        self.url = reverse(enter_data, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })

    def _running_enketo(self):
        if hasattr(settings, 'ENKETO_URL') and \
            self._check_url(settings.ENKETO_URL):
            return True
        return False

    def test_running_enketo(self):
        exist = self._running_enketo()
        self.assertTrue(exist)

    def test_enter_data_redir(self):
        response = self.client.get(self.url)
        #make sure response redirect to an enketo site
        enketo_base_url = urlparse(settings.ENKETO_URL).netloc
        redirected_base_url = urlparse(response['Location']).netloc
        #TODO: checking if the form is valid on enketo side
        self.assertIn(enketo_base_url, redirected_base_url)
        self.assertEqual(response.status_code, 302)

    def test_enter_data_no_permission(self):
        response = self.anon.get(self.url)
        status_code = 200 if self._running_enketo() else 403
        self.assertEqual(response.status_code, 403)

    def test_public_with_link_to_share_toggle_on(self):
        response = self.client.post(self.perm_url, {'for_user': 'all',
            'perm_type': 'link'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(MetaData.public_link(self.xform), True)
        response = self.anon.get(self.show_url)
        self.assertEqual(response.status_code, 302)
        response = self.anon.get(self.url)
        status_code = 200 if self._running_enketo() else 403
        self.assertEqual(response.status_code, status_code)
