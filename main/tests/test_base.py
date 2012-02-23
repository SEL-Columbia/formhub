import os
from django.test import TestCase
from django.contrib.auth.models import User
from django.test.client import Client
from odk_logger.models import XForm

class MainTestCase(TestCase):

    def setUp(self):
        self.maxDiff = None
        self._create_user_and_login()

    def _create_user(self, username, password):
        user, created = User.objects.get_or_create(username=username)
        user.set_password(password)
        user.save()
        return user

    def _login(self, username, password):
        client = Client()
        assert client.login(username=username, password=password)
        return client

    def _create_user_and_login(self, username="bob", password="bob"):
        self.user = self._create_user(username, password)
        self.client = self._login(username, password)
        self.anon = Client()

    this_directory = os.path.dirname(__file__)

    def _publish_xls_file(self, path):
        if not path.startswith('/%s/' % self.user.username):
            path = os.path.join(self.this_directory, path)
        with open(path) as xls_file:
            post_data = {'xls_file': xls_file}
            return self.client.post('/%s/' % self.user.username, post_data)

    def _publish_transporation_form(self):
        xls_path = os.path.join(self.this_directory, "fixtures",
                "transportation", "transportation.xls")
        count = XForm.objects.count()
        response = self._publish_xls_file(xls_path)
        self.assertEqual(XForm.objects.count(), count + 1)
        self.xform = XForm.objects.all().reverse()[0]

    def _make_submission(self, path):
        with open(path) as f:
            post_data = {'xml_submission_file': f}
            url = '/%s/submission' % self.user.username
            self.response = self.anon.post(url, post_data)

