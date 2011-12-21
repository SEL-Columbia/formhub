from test_base import MainTestCase
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

