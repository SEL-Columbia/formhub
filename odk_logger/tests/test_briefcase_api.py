import os
import codecs

from django.core.urlresolvers import reverse

from main.tests.test_base import MainTestCase

from odk_logger.views import view_submission_list
from odk_logger.models import Instance


class TestBriefcaseAPI(MainTestCase):
    def setUp(self):
        super(MainTestCase, self).setUp()
        self._create_user_and_login()
        self._publish_transportation_form()
        self._make_submissions()
        self._submission_list_url = reverse(
            view_submission_list,
            kwargs={'username': self.user.username})

    def test_view_submissionList(self):
        response = self.client.get(
            self._submission_list_url,
            data={'formId': self.xform.id_string})
        self.assertEqual(response.status_code, 200)
        submission_list_path = os.path.join(
            self.this_directory, 'fixtures', 'transportation',
            'view', 'submissionList.xml')
        instances = Instance.objects.filter(xform=self.xform)
        self.assertTrue(instances.count() > 0)
        last_index = instances[instances.count() - 1].pk
        with codecs.open(submission_list_path, 'rb', encoding='utf-8') as f:
            expected_submission_list = f.read()
            expected_submission_list = \
                expected_submission_list.replace(
                    '{{resumptionCursor}}', '%s' % last_index)
            self.assertEqual(response.content, expected_submission_list)

    def test_view_submissionList_numEntries(self):
        params = {'formId': self.xform.id_string}
        params['numEntries'] = 2
        instances = Instance.objects.filter(xform=self.xform)
        self.assertTrue(instances.count() > 1)
        last_index = instances[:2][1].pk
        for index in range(1, 3):
            response = self.client.get(
                self._submission_list_url,
                data=params)
            self.assertEqual(response.status_code, 200)
            # set cursor for second request
            params['cursor'] = last_index
            submission_list_path = os.path.join(
                self.this_directory, 'fixtures', 'transportation',
                'view', 'submissionList-%s.xml' % index)
            with codecs.open(submission_list_path, encoding='utf-8') as f:
                expected_submission_list = f.read()
                expected_submission_list = \
                    expected_submission_list.replace(
                        '{{resumptionCursor}}', '%s' % last_index)
                self.assertEqual(response.content, expected_submission_list)
            last_index += 2
