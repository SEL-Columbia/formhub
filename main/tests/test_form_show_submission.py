from test_base import MainTestCase
from main.views import home, show_submission
from odk_viewer.views import survey_responses
from django.core.urlresolvers import reverse
from guardian.shortcuts import assign

class TestFormShowSubmission(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        self._create_user_and_login()
        self._publish_transporation_form_and_submit_instance()
        self.submission= self.xform.surveys.reverse()[0]
        self.url = reverse(show_submission, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string,
            'uuid': self.submission.uuid,
        })
        self.survey_url = reverse(survey_responses, kwargs={
                'pk': self.submission.parsed_instance.pk })

    def test_get_form_by_uuid(self):
        response = self.client.get(self.url)
        self.assertEquals(response.status_code, 302)
        self.assertEquals(self.base_url + self.survey_url, response['Location'])

    def test_no_anon_get_form_by_uuid(self):
        response = self.anon.get(self.url)
        self.assertEquals(response.status_code, 302)
        self.assertEquals(self.base_url + reverse(home), response['Location'])

    def test_no_without_perm_get_form_by_uuid(self):
        self._create_user_and_login('alice', 'alice')
        response = self.client.get(self.url)
        self.assertEquals(response.status_code, 302)
        self.assertEquals(self.base_url + reverse(home), response['Location'])

    def test_with_perm_get_form_by_uuid(self):
        self._create_user_and_login('alice', 'alice')
        assign('view_xform', self.user, self.xform)
        response = self.client.get(self.url)
        self.assertEquals(response.status_code, 302)
        self.assertEquals(self.base_url + self.survey_url, response['Location'])
