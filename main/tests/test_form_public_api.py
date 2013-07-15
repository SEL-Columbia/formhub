import json

from django.core.urlresolvers import reverse

from test_base import MainTestCase
from main.views import public_api


class TestFormPublicAPI(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        self._create_user_and_login()
        self._publish_transportation_form_and_submit_instance()
        self.public_api_url = reverse(public_api, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })

    def test_api(self):

        response = self.client.get(self.public_api_url, {})
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        for field in ('username', 'id_string', 'bamboo_dataset', 'shared',
                      'shared_data', 'downloadable', 'is_crowd_form',
                      'title', 'date_created', 'date_modified', 'uuid'):
            self.assertIn(field, data)

        self.assertEqual(data.get('username'), self.user.username)
        self.assertEqual(data.get('id_string'), self.xform.id_string)
