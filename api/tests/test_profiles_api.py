from api.tests.test_api import IntegrationTestAPICase


class IntegrationTestProfileAPI(IntegrationTestAPICase):

    def test_profiles_list(self):
        self._login_user_and_profile()
        response = self.client.get('/api/v1/profiles')
        data = [
            {
                'url': 'http://testserver/api/v1/profiles/bob',
                'username': u'bob',
                'name': u'Bob',
                'email': u'bob@columbia.edu',
                'city': u'Bobville',
                'country': u'US',
                'organization': u'Bob Inc.',
                'website': u'bob.com',
                'twitter': u'boberama',
                'gravatar': self.user.profile.gravatar,
                'require_auth': False,
                'user': 'http://testserver/api/v1/users/bob'
            }
        ]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, data)

    def test_profiles_get(self):
        self._login_user_and_profile()
        response = self.client.get('/api/v1/profiles/bob')
        data = {
            'url': 'http://testserver/api/v1/profiles/bob',
            'username': u'bob',
            'name': u'Bob',
            'email': u'bob@columbia.edu',
            'city': u'Bobville',
            'country': u'US',
            'organization': u'Bob Inc.',
            'website': u'bob.com',
            'twitter': u'boberama',
            'gravatar': self.user.profile.gravatar,
            'require_auth': False,
            'user': 'http://testserver/api/v1/users/bob'
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, data)
