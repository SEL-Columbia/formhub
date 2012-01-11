from test_base import MainTestCase
from test_user_profile import TestUserProfile
from django.test.client import Client
from django.contrib.auth.models import User
from main.models import UserProfile

class TestUserLogin(MainTestCase):
    def test_any_case_login_ok(self):
        username = 'bob'
        password = 'bobbob'
        self._create_user(username, password)
        self._login('BOB', password)

    def test_username_is_made_lower_case(self):
        username = 'ROBERT'
        password = 'bobbob'
        self._create_user(username, password)
        self._login('robert', password)

    def test_redirect_if_logged_in(self):
        self._create_user_and_login()
        response = self.client.get('')
        self.assertEqual(response.status_code, 302)

class TestUserReservedNames(TestUserProfile):
    def test_disallow_reserved_names(self):
        username = 'forms'
        password = 'bobbob'
        self._login_user_and_profile({ 'username': username })
        self.assertEqual(len(User.objects.all()), 0)

