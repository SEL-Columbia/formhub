import os
import codecs

from django.core.urlresolvers import reverse

from main.tests.test_base import MainTestCase

from odk_logger.views import view_submission_list


class TestBriefcaseAPI(MainTestCase):
    def setUp(self):
        super(MainTestCase, self).setUp()
        self._create_user_and_login()
        self._publish_transportation_form()
        self._make_submissions()

    def test_view_submissionList(self):
        response = self.client.get(
            reverse(
                view_submission_list,
                kwargs={'username': self.user.username}),
            data={'formId': self.xform.id_string})
        self.assertEqual(response.status_code, 200)
        submission_list_path = os.path.join(
            self.this_directory, 'fixtures', 'transportation',
            'view', 'submissionList.xml')
        with codecs.open(submission_list_path, 'rb', encoding='utf-8') as f:
            expected_submission_list = f.read()
            self.assertEqual(response.content, expected_submission_list)
