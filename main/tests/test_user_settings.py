from test_base import MainTestCase
from main.models import UserProfile
from django.core.urlresolvers import reverse
from main.views import profile_settings

class TestUserSettings(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        self.settings_url = reverse(profile_settings, kwargs={'username': self.user.username})

    def test_render_user_settings(self):
        response = self.client.get(self.settings_url)
        self.assertEqual(response.status_code, 200)

    def test_show_existing_profile_data(self):
        profile, created = UserProfile.objects.get_or_create(user=self.user)
        profile.name = "Bobby"
        profile.save()
        response = self.client.get(self.settings_url)
        self.assertContains(response, profile.name)

    def test_update_user_settings(self):
        post_data = {
            'name': 'Bobby',
            'organization': 'Bob Inc',
            'city': 'Bobville',
            'country': 'BB',
            'twitter': 'bobo',
            'home_page': 'bob.com',
            'require_auth': True,
            'email': 'bob@bob.com'
        }
        response = self.client.post(self.settings_url, post_data)
        self.assertEqual(response.status_code, 302)
        self.user = UserProfile.objects.get(pk=self.user.profile.pk).user
        for key, value in post_data.iteritems():
            try:
                self.assertEqual(self.user.profile.__dict__[key], value)
            except KeyError, e:
                if key == 'email':
                    users = UserProfile.objects.all()
                    self.assertEqual(self.user.__dict__[key], value)
                else:
                    raise e

