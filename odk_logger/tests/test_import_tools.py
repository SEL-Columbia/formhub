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


def images_count():
    images = glob.glob(os.path.join(settings.MEDIA_ROOT, 'attachments', '*'))
    return len(images)


class TestImportingDatabase(MainTestCase):
    def setUp(self):
        MainTestCase.setUp(self)
    
    def tearDown(self):
        # delete everything we imported
        Instance.objects.all().delete() # ?
        if settings.TESTING_MODE:
            images = glob.glob(os.path.join(settings.MEDIA_ROOT, 'attachments', '*'))
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
        import_instances_from_zip(os.path.join(DB_FIXTURES_PATH, "bulk_submission.zip"), self.user)

        initial_instance_count = Instance.objects.count()
        initial_image_count = images_count()

        import_instances_from_zip(os.path.join(DB_FIXTURES_PATH, "bulk_submission.zip"), self.user)

        final_instance_count = Instance.objects.count()
        final_image_count = images_count()

        #Images are not duplicated
        # TODO: Figure out how to get this test passing.
        self.assertEqual(initial_image_count, final_image_count)

        # Instance count should have incremented
        # by 1 (or 2) based on the b1 & b2 data sets
        self.assertEqual(initial_instance_count, final_instance_count)

