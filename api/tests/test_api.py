from django.test import TestCase
from django.contrib.auth.models import User


class IntegrationTestAPICase(TestCase):
    def _login_user_and_profile(self, extra_post_data={}):
        post_data = {
            'username': 'bob',
            'email': 'bob@columbia.edu',
            'password1': 'bobbob',
            'password2': 'bobbob',
            'name': 'Bob',
            'city': 'Bobville',
            'country': 'US',
            'organization': 'Bob Inc.',
            'home_page': 'bob.com',
            'twitter': 'boberama'
        }
        url = '/accounts/register/'
        post_data = dict(post_data.items() + extra_post_data.items())
        self.response = self.client.post(url, post_data)
        try:
            self.user = User.objects.get(username=post_data['username'])
        except User.DoesNotExist:
            pass
        else:
            self.user.is_active = True
            self.user.save()
            self.assertTrue(
                self.client.login(username=self.user.username,
                                  password='bobbob'))
