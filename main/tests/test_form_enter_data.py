from test_base import MainTestCase
from odk_logger.views import enter_data
from django.core.urlresolvers import reverse
from odk_logger.models import XForm

class TestFormEnterData(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        self._create_user_and_login()
        self._publish_transporation_form_and_submit_instance()
        self.url = reverse(enter_data, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })

    def test_enter_data_redir(self):
        response = self.client.get(self.url)
        # because webforms is not running here
        self.assertEqual(response.status_code, 302)
