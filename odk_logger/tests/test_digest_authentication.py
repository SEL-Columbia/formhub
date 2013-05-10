import os

from django_digest.test import Client as DigestClient
from main.tests.test_base import MainTestCase


class TestDigestAuthentication(MainTestCase):
    def setUp(self):
        super(MainTestCase, self).setUp()
        self._create_user_and_login()
        self._publish_transportation_form()

    def test_authenticated_submissions(self):
        """
        xml_submission_file is the field name for the posted xml file.
        """
        s = self.surveys[0]
        xml_submission_file_path = os.path.join(
            self.this_directory, 'fixtures',
            'transportation', 'instances', s, s + '.xml'
        )
        # authenticate first
        #url = '/%s/submission' % self.user.username
        url = '/submission'
        extra = {
            'REQUEST_METHOD': 'HEAD',
        }

        client = DigestClient()
        # request with no credentials
        req = client.get(url, {}, **extra)
        self.assertEqual(req.status_code, 401)
        # apply credentials
        client.set_authorization('bob', 'bob', 'Digest')
        req = client.get(url, {}, **extra)
        # if 204 authorization successfull, proceed
        self.assertEqual(req.status_code, 204)
        # submissions should use this authenticated client
        self.anon = client
        self._make_submission(xml_submission_file_path, add_uuid=True)
        self.assertEqual(self.response.status_code, 201)
