from django.core.urlresolvers import reverse
from main.tests.test_base import MainTestCase
from odk_viewer.views import attachment_url
from guardian.shortcuts import assign, remove_perm

class TestAttachmentUrl(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        self._create_user_and_login()
        self._publish_transportation_form()
        self._submit_transport_instance_w_attachment()
        self.url = reverse(attachment_url)

    def test_attachment_url(self):
        response = self.client.get(self.url, {"media_file": self.attachment_media_file})
        self.assertEqual(response.status_code, 302) #redirects to amazon

    def test_attachment_not_found(self):
        response = self.client.get(self.url, {"media_file": "non_existent_attachment.jpg"})
        self.assertEqual(response.status_code, 404) #redirects to amazon

