from main.tests.test_base import MainTestCase
#from django.test import TestCase
from odk_logger.models import Instance
import os
import glob

from odk_logger.import_tools import import_instances_from_zip

CUR_PATH = os.path.abspath(__file__)
CUR_DIR = os.path.dirname(CUR_PATH)
DB_FIXTURES_PATH = os.path.join(CUR_DIR, 'data_from_sdcard')

from django.conf import settings


def images_count(username="bob"):
    images = glob.glob(
        os.path.join(settings.MEDIA_ROOT, username, 'attachments', '*'))
    return len(images)


class TestImportingDatabase(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        self._publish_xls_file(
            os.path.join(
                settings.PROJECT_ROOT,
                "odk_logger", "fixtures", "test_forms", "tutorial.xls"))

    def tearDown(self):
        # delete everything we imported
        Instance.objects.all().delete()  # ?
        if settings.TESTING_MODE:
            images = glob.glob(
                os.path.join(
                    settings.MEDIA_ROOT, self.user.username, 'attachments', '*'))
            for image in images:
                os.remove(image)

    def test_importing_b1_and_b2(self):
        """
        b1 and b2 are from the *same phone* at different times. (this
        might not be a realistic test)

        b1:
        1 photo survey (completed)
        1 simple survey (not marked complete)

        b2:
        1 photo survey (duplicate, completed)
        1 simple survey (marked as complete)
        """
        # import from sd card
        initial_instance_count = Instance.objects.count()
        initial_image_count = images_count()

        import_instances_from_zip(os.path.join(
            DB_FIXTURES_PATH, "bulk_submission.zip"), self.user)

        instance_count = Instance.objects.count()
        image_count = images_count()
        #Images are not duplicated
        # TODO: Figure out how to get this test passing.
        self.assertEqual(image_count, initial_image_count + 2)

        # Instance count should have incremented
        # by 1 (or 2) based on the b1 & b2 data sets
        self.assertEqual(instance_count, initial_instance_count + 2)

    def test_badzipfile_import(self):
        total, success, errors = import_instances_from_zip(
            os.path.join(
                CUR_DIR, "Water_Translated_2011_03_10.xml"), self.user)
        self.assertEqual(total, 0)
        self.assertEqual(success, 0)
        expected_errors = [u'File is not a zip file']
        self.assertEqual(errors, expected_errors)
