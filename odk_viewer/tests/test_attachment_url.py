import os

from django.core.urlresolvers import reverse
from django.conf import settings
from main.tests.test_base import MainTestCase
from odk_logger.models import Attachment
from odk_viewer.views import attachment_url


class TestAttachmentUrl(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        self._create_user_and_login()
        self._publish_transportation_form()
        self._submit_transport_instance_w_attachment()
        self.url = reverse(attachment_url)

    def test_attachment_url(self):
        response = self.client.get(
            self.url, {"media_file": self.attachment_media_file})
        print response
        print response.content
        print self.url
        print self.attachment_media_file
        self.assertEqual(response.status_code, 302) #redirects to amazon

    def test_attachment_not_found(self):
        response = self.client.get(
            self.url, {"media_file": "non_existent_attachment.jpg"})
        self.assertEqual(response.status_code, 404)

    def test_attachment_has_mimetype(self):
        attachment = Attachment.objects.all().reverse()[0]
        self.assertEqual(attachment.mimetype, 'image/jpeg')

    def tearDown(self):
        path = os.path.join(settings.MEDIA_ROOT, self.user.username)
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))

