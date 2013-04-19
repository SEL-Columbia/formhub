import os
import codecs

from django.core.urlresolvers import reverse

from main.tests.test_base import MainTestCase

from odk_logger.views import view_submission_list
from odk_logger.views import view_download_submission
from odk_logger.models import Instance


class TestBriefcaseAPI(MainTestCase):
    def setUp(self):
        super(MainTestCase, self).setUp()
        self._create_user_and_login()
        self._publish_transportation_form()
        self._submission_list_url = reverse(
            view_submission_list,
            kwargs={'username': self.user.username})
        self._download_submission_url = reverse(
            view_download_submission,
            kwargs={'username': self.user.username})

    def test_view_submissionList(self):
        self._make_submissions()
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
        self._make_submissions()
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

    def test_view_downloadSubmission(self):
        self.maxDiff = None
        self._submit_transport_instance_w_attachment()
        instanceId = u'5b2cc313-fc09-437e-8149-fcd32f695d41'
        formId = u'%(formId)s[@version=null and @uiVersion=null]/' \
                 u'%(formId)s[@key=uuid:%(instanceId)s]' % {
                 'formId': self.xform.id_string,
                 'instanceId': instanceId}
        params = {'formId': formId}
        response = self.client.get(self._download_submission_url, data=params)
        text = "uuid:%s" % instanceId
        download_submission_path = os.path.join(
            self.this_directory, 'fixtures', 'transportation',
            'view', 'downloadSubmission.xml')
        with codecs.open(download_submission_path, encoding='utf-8') as f:
            text = f.read()
            self.assertContains(response, instanceId, status_code=200)
            self.assertMultiLineEqual(response.content, text)
