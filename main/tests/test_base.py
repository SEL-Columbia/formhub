import base64
import os
import re
from tempfile import NamedTemporaryFile
import urllib2

from django.contrib.auth.models import User
# from django.test import TestCase
from django_nose import FastFixtureTestCase as TestCase
from django.test.client import Client

from odk_logger.models import XForm, Instance, Attachment
import urllib2
from settings import _MONGO_CONNECTION, MONGO_TEST_DB_NAME


class MainTestCase(TestCase):

    surveys = ['transport_2011-07-25_19-05-49',
               'transport_2011-07-25_19-05-36',
               'transport_2011-07-25_19-06-01',
               'transport_2011-07-25_19-06-14']

    def setUp(self):
        self.maxDiff = None
        self._create_user_and_login()
        self.base_url = 'http://testserver'

    def tearDown(self):
        # clear mongo db after each test
        _MONGO_CONNECTION[MONGO_TEST_DB_NAME].instances.drop()

    def _create_user(self, username, password):
        user, created = User.objects.get_or_create(username=username)
        user.set_password(password)
        user.save()
        return user

    def _login(self, username, password):
        client = Client()
        assert client.login(username=username, password=password)
        return client

    def _logout(self, client=None):
        if not client:
            client = self.client
        client.logout()

    def _create_user_and_login(self, username="bob", password="bob"):
        self.login_username = username
        self.login_password = password
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

    def _publish_xlsx_file(self):
        path = os.path.join(self.this_directory, 'fixtures', 'exp.xlsx')
        pre_count = XForm.objects.count()
        response = MainTestCase._publish_xls_file(self, path)
        # make sure publishing the survey worked
        self.assertEqual(response.status_code, 200)
        self.assertEqual(XForm.objects.count(), pre_count + 1)

    def _publish_xls_file_and_set_xform(self, path):
        count = XForm.objects.count()
        self.response = self._publish_xls_file(path)
        self.assertEqual(XForm.objects.count(), count + 1)
        self.xform = XForm.objects.order_by('pk').reverse()[0]

    def _share_form_data(self, id_string='transportation_2011_07_25'):
        xform = XForm.objects.get(id_string=id_string)
        xform.shared_data = True
        xform.save()

    def _publish_transportation_form(self):
        xls_path = os.path.join(self.this_directory, "fixtures",
                "transportation", "transportation.xls")
        count = XForm.objects.count()
        response = MainTestCase._publish_xls_file(self, xls_path)
        self.assertEqual(XForm.objects.count(), count + 1)
        self.xform = XForm.objects.order_by('pk').reverse()[0]

    def _submit_transport_instance(self, survey_at=0):
        s = self.surveys[survey_at]
        self._make_submission(os.path.join(self.this_directory, 'fixtures',
                    'transportation', 'instances', s, s + '.xml'))

    def _submit_transport_instance_w_uuid(self, name):
        self._make_submission(os.path.join(self.this_directory, 'fixtures',
            'transportation', 'instances_w_uuid', name, name + '.xml'))

    def _submit_transport_instance_w_attachment(self, survey_at=0):
        s = self.surveys[survey_at]
        media_file = "1335783522563.jpg"
        self._make_submission_w_attachment(os.path.join(self.this_directory, 'fixtures',
            'transportation', 'instances', s, s + '.xml'), os.path.join(self.this_directory, 'fixtures',
            'transportation', 'instances', s, media_file))
        attachment = Attachment.objects.all().reverse()[0]
        self.attachment_media_file = attachment.media_file

    def _publish_transportation_form_and_submit_instance(self):
        self._publish_transportation_form()
        self._submit_transport_instance()

    def _make_submission(self, path, username=None, add_uuid=False,
                         touchforms=False, forced_submission_time=None):
        # store temporary file with dynamic uuid
        tmp_file = None
        if add_uuid and not touchforms:
            tmp_file = NamedTemporaryFile(delete=False)
            split_xml = None
            with open(path) as _file:
                split_xml = re.split(r'(<transport>)', _file.read())
            split_xml[1:1] = [
                '<formhub><uuid>%s</uuid></formhub>' % self.xform.uuid
            ]
            tmp_file.write(''.join(split_xml))
            path = tmp_file.name
            tmp_file.close()

        with open(path) as f:
            post_data = {'xml_submission_file': f}

            if username is None:
                username = self.user.username
            url = '/%s/submission' % username

            # touchforms submission
            if add_uuid and touchforms:
                post_data['uuid'] = self.xform.uuid
            if touchforms:
                url ='/submission'  # touchform has no username
            self.response = self.anon.post(url, post_data)

        if forced_submission_time:
            instance = Instance.objects.order_by('-pk').all()[0]
            instance.date_created = forced_submission_time
            instance.save()
            instance.parsed_instance.save()
        # remove temporary file if stored
        if add_uuid and not touchforms:
            os.unlink(tmp_file.name)

    def _make_submission_w_attachment(self, path, attachment_path):
        with open(path) as f:
            a = open(attachment_path)
            post_data = {'xml_submission_file': f, 'media_file': a}
            url = '/%s/submission' % self.user.username
            self.response = self.anon.post(url, post_data)

    def _make_submissions(self, username=None, add_uuid=False, should_store=True):
        paths = [os.path.join(self.this_directory, 'fixtures', 'transportation',
                'instances', s, s + '.xml') for s in self.surveys]
        pre_count = Instance.objects.count()
        for path in paths:
            self._make_submission(path, username, add_uuid)
        post_count = pre_count + len(self.surveys) if should_store\
            else pre_count
        self.assertEqual(Instance.objects.count(), post_count)
        self.assertEqual(self.xform.surveys.count(), post_count)

    def _check_url(self, url, timeout=1):
        try:
            response = urllib2.urlopen(url, timeout=timeout)
            return True
        except urllib2.URLError as err: pass
        return False

    def _internet_on(self, url='http://74.125.113.99'):
        # default value is some google IP
        return self._check_url(url)

    def _set_auth_headers(self, username, password):
        return {
            'HTTP_AUTHORIZATION': 'Basic ' + base64.b64encode('%s:%s' % (username, password)),
            }
