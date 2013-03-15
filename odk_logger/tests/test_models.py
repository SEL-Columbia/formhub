import os

from django.core.files.base import File

from odk_logger.models import Attachment, Instance

from main.tests.test_base import MainTestCase


class AttachmentTest(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        self._publish_transportation_form_and_submit_instance()
        media_file = "1335783522563.jpg"
        media_file = os.path.join(
            self.this_directory, 'fixtures',
            'transportation', 'instances', self.surveys[0], media_file)
        instance = Instance.objects.all()[0]
        self.attachment = Attachment.objects.create(
            instance=instance, media_file=File(open(media_file), media_file))

    def test_mimetype(self):
        self.assertEqual(self.attachment.mimetype, 'image/jpeg')

