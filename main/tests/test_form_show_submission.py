from test_base import MainTestCase
from main.views import show_submission
from django.core.urlresolvers import reverse

class TestFormShowSubmission(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        self._create_user_and_login()
        self._publish_transporation_form_and_submit_instance()
        self.instance = self.xform.surveys.reverse()[0]
        self.url = reverse(show_submission, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string,
            'uuid': self.instance.uuid,
        })

    def test_get_form_by_uuid(self):
        response = self.client.get(self.url)
        self.assertEquals(response.status_code, 302)
