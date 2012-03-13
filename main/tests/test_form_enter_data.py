from test_base import MainTestCase
from odk_logger.views import enter_data
from django.core.urlresolvers import reverse
from odk_logger.models import XForm
from main.views import set_perm, show
from main.models import MetaData

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

    def test_enter_data_redir(self):
        response = self.client.get(self.url)
        # because webforms is not running here
        self.assertEqual(response.status_code, 302)

    def test_enter_data_no_permission(self):
        response = self.anon.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_public_with_link_to_share_toggle_on(self):
        response = self.client.post(self.perm_url, {'for_user': 'all',
            'perm_type': 'link'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(MetaData.public_link(self.xform), True)
        response = self.anon.get(self.show_url)
        self.assertEqual(response.status_code, 302)
        response = self.anon.get(self.url)
        self.assertEqual(response.status_code, 302)
