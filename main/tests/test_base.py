import os
from django.test import TestCase
from django.contrib.auth.models import User
from django.test.client import Client
from odk_logger.models import XForm, Instance

class MainTestCase(TestCase):

    def setUp(self):
        self.maxDiff = None
        self._create_user_and_login()
        self.base_url = 'http://testserver'

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

    def _publish_transportation_form(self):
        xls_path = os.path.join(self.this_directory, "fixtures",
                "transportation", "transportation.xls")
        count = XForm.objects.count()
        response = MainTestCase._publish_xls_file(self, xls_path)
        self.assertEqual(XForm.objects.count(), count + 1)
        self.xform = XForm.objects.all().reverse()[0]

    def _submit_transport_instance(self):
        s = 'transport_2011-07-25_19-05-49'
        self._make_submission(os.path.join(self.this_directory, 'fixtures',
                    'transportation', 'instances', s, s + '.xml'))

    def _publish_transportation_form_and_submit_instance(self):
        self._publish_transportation_form()
        self._submit_transport_instance()

    def _make_submission(self, path):
        with open(path) as f:
            post_data = {'xml_submission_file': f}
            url = '/%s/submission' % self.user.username
            self.response = self.anon.post(url, post_data)

    def _make_submissions(self):
        surveys = ['transport_2011-07-25_19-05-49',
                   'transport_2011-07-25_19-05-36',
                   'transport_2011-07-25_19-06-01',
                   'transport_2011-07-25_19-06-14',]
        paths = [os.path.join(self.this_directory, 'fixtures', 'transportation',
                'instances', s, s + '.xml') for s in surveys]
        pre_count = Instance.objects.count()
        for path in paths:
            self._make_submission(path)
        self.assertEqual(Instance.objects.count(), pre_count + 4)
        self.assertEqual(self.xform.surveys.count(), pre_count + 4)
