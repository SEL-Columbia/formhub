from test_base import MainTestCase
from main.models import UserProfile

class TestUserSettings(MainTestCase):

    def test_render_user_settings(self):
        settings_url = "/%s/settings" % self.user.username
        response = self.client.get(settings_url)
        self.assertEqual(response.status_code, 200)

    def test_show_existing_profile_data(self):
        profile, created = UserProfile.objects.get_or_create(user=self.user)
        profile.name = "Bobby"
        profile.save()
        settings_url = "/%s/settings" % self.user.username
        response = self.client.get(settings_url)
        self.assertContains(response, profile.name)

    def test_update_user_settings(self):
        settings_url = "/%s/settings" % self.user.username
        post_data = {
            'name': 'Bobby',
            'organization': 'Bob Inc',
            'city': 'Bobville',
            'country': 'BB',
            'twitter': 'bobo',
            'home_page': 'bob.com',
        }
        response = self.client.post(settings_url, post_data)
        self.assertEqual(response.status_code, 302)
        for key, value in post_data.iteritems():
            self.assertEqual(eval('self.user.profile.%s' % key), value)

