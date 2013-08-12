import json
from api.tests.test_api import IntegrationTestAPICase


class IntegrationTestUserAPI(IntegrationTestAPICase):

    def test_user_list(self):
        self._login_user_and_profile()
        response = self.client.get('/api/v1/users')
        data = [{'username': u'bob', 'first_name': u'Bob', 'last_name': u''}]
        self.assertContains(response, json.dumps(data))

    def test_user_get(self):
        self._login_user_and_profile()
        response = self.client.get('/api/v1/users/bob')
        data = {'username': u'bob', 'first_name': u'Bob', 'last_name': u''}
        self.assertContains(response, json.dumps(data))
