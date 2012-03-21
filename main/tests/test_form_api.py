from django.core.urlresolvers import reverse

from test_base import MainTestCase
from main.views import api

class TestFormAPI(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        self._create_user_and_login()
        self._publish_transportation_form_and_submit_instance()
        self.api_url = reverse(api, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })

    def test_api(self):
        pass
