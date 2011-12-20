from test_base import MainTestCase
from django.contrib.auth.models import User
from main.models import UserProfile

class TestUserProfile(MainTestCase):
    def setup(self):
        self.client = Client()

    def _create_user_and_profile(self):
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
        self.response = self.client.post(url, post_data)

    def test_create_user_with_given_name(self):
        self._create_user_and_profile()
        raise Exception(self.response.content)
        self.assertEqual(User.objects.all()[0].username, 'bob')

    def test_create_user_profile_for_user(self):
        self._create_user_and_profile()
        raise Exception(self.response.content)
        raise Exception(UserProfile.objects.all())
        profile = User.objects.all()[0].profile
        self.assertEqual(profile.city, 'Bobville')

