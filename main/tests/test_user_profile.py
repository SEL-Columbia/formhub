from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from main.models import UserProfile
from main.views import profile

# do not inherit from MainTestCase because we don't want auto login
class TestUserProfile(TestCase):
    def setup(self):
        self.client = Client()
        self.assertEqual(len(User.objects.all()), 0)

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
        self.response = self.client.post(url,
            dict(post_data.items() + extra_post_data.items()))

    def test_create_user_with_given_name(self):
        self._login_user_and_profile()
        self.assertEqual(self.response.status_code, 302)
        self.assertEqual(User.objects.all()[0].username, 'bob')

    def test_create_user_profile_for_user(self):
        self._login_user_and_profile()
        self.assertEqual(self.response.status_code, 302)
        profile = User.objects.all()[0].profile
        self.assertEqual(profile.city, 'Bobville')

    def test_disallow_non_alpha_numeric(self):
        invalid_usernames = [
            'b ob',
            'b.o.b.',
            'b-ob',
            'b!',
            '@bob',
            'bob@bob.com',
            'bob$',
            'b&o&b',
            'bob?',
            '#bob',
            '(bob)',
            'b*ob',
            '%s % bob',
        ]
        users_before = User.objects.count()
        for username in invalid_usernames:
            self._login_user_and_profile({ 'username': username })
            self.assertEqual(User.objects.count(), users_before)

    def test_disallow_reserved_name(self):
        users_before = User.objects.count()
        self._login_user_and_profile({ 'username': 'admin' })
        self.assertEqual(User.objects.count(), users_before)

    def test_404_if_user_does_not_exist(self):
        response = self.client.get(reverse(profile,
            kwargs={'username': 'nonuser'}))
        self.assertEqual(response.status_code, 404)
