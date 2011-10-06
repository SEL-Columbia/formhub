from django.test import TestCase
from django.contrib.auth.models import User
from django.test.client import Client


class MainTestCase(TestCase):

    def _create_user(self, username, password):
        user = User.objects.create(username=username)
        user.set_password(password)
        user.save()
        return user

    def _login(self, username, password):
        client = Client()
        assert client.login(username=username, password=password)
        return client

    def _create_user_and_login(self, username="bob", password="bob"):
        self.user = self._create_user(username, password)
        self.bob = self._login(username, password)
        self.anon = Client()

    def _publish_xls_file(self, path):
        with open(path) as xls_file:
            post_data = {'xls_file': xls_file}
            return self.bob.post('/', post_data)

    def _make_submission(self, path):
        with open(path) as f:
            post_data = {'xml_submission_file': f}
            self.anon.post('/bob/submission', post_data)
