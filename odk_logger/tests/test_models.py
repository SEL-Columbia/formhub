import os

from datetime import datetime

from django.core.files.base import File
from django.core.files.storage import default_storage
from django.core.management import call_command

from odk_logger.models import Attachment, Instance

from utils.image_tools import image_url

from main.tests.test_base import MainTestCase


class AttachmentTest(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        self._publish_transportation_form_and_submit_instance()
        self.media_file = "1335783522563.jpg"
        media_file = os.path.join(
            self.this_directory, 'fixtures',
            'transportation', 'instances', self.surveys[0], self.media_file)
        self.instance = Instance.objects.all()[0]
        self.attachment = Attachment.objects.create(
            instance=self.instance,
            media_file=File(open(media_file), media_file))

    def test_mimetype(self):
        self.assertEqual(self.attachment.mimetype, 'image/jpeg')

    def test_thumbnails(self):
        for attachment in Attachment.objects.filter(instance=self.instance):
            url = image_url(attachment, 'small')
            filename = attachment.media_file.name.replace('.jpg', '')
            thumbnail = '%s-small.jpg' % filename
            self.assertNotEqual(
                url.find(thumbnail), -1)
            for size in ['small', 'medium', 'large']:
                thumbnail = '%s-%s.jpg' % (filename, size)
                self.assertTrue(
                    default_storage.exists(thumbnail))
                default_storage.delete(thumbnail)

    def test_create_thumbnails_command(self):
        call_command("create_image_thumbnails")
        for attachment in Attachment.objects.filter(instance=self.instance):
            filename = attachment.media_file.name.replace('.jpg', '')
            for size in ['small', 'medium', 'large']:
                thumbnail = '%s-%s.jpg' % (filename, size)
                self.assertTrue(
                    default_storage.exists(thumbnail))
        check_datetime = datetime.now()
        # replace or regenerate thumbnails if they exist
        call_command("create_image_thumbnails", force=True)
        for attachment in Attachment.objects.filter(instance=self.instance):
            filename = attachment.media_file.name.replace('.jpg', '')
            for size in ['small', 'medium', 'large']:
                thumbnail = '%s-%s.jpg' % (filename, size)
                self.assertTrue(
                    default_storage.exists(thumbnail))
                self.assertTrue(
                    default_storage.modified_time(thumbnail) > check_datetime)
                default_storage.delete(thumbnail)
