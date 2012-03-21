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
    images = glob.glob(os.path.join(settings.MEDIA_ROOT, username, 'attachments', '*'))
    return len(images)


class TestImportingDatabase(MainTestCase):
    def setUp(self):
        MainTestCase.setUp(self)
        self._publish_xls_file(
                               os.path.join(settings.PROJECT_ROOT, \
                                    "odk_logger", "fixtures", "test_forms", "tutorial.xls"))
    
    def tearDown(self):
        # delete everything we imported
        Instance.objects.all().delete() # ?
        if settings.TESTING_MODE:
            images = glob.glob(os.path.join(settings.MEDIA_ROOT, 'attachments', '*'))
            for image in images:
                os.remove(image)
    def test_importing_1_1_5(self):
        """
        bulk_submission_1-1-5.zip has an ODK directory from
        a device using ODK Collect 1.1.5.

        The metadata is in "odk/metadata/data".
        """
        # import from sd card
        import_instances_from_zip(os.path.join(DB_FIXTURES_PATH, "bulk_submission_1-1-5.zip"), self.user)

        instance_count = Instance.objects.count()
        image_count = images_count()

        statii = sorted([x['status'] for x in Instance.objects.all().values('status')])

        # one of the imported surveys is "complete"
        self.assertEqual(statii[0], "complete")

        # one of the imported surveys is "incomplete"
        self.assertEqual(statii[1], "incomplete")

        #Images are not duplicated
        # TODO: Figure out how to get this test passing.
        self.assertEqual(image_count, 2)

        #Instance count should have incremented
        # by 1 (or 2) based on the b1 & b2 data sets
        self.assertEqual(instance_count, 2)

    def test_importing_1_1_7(self):
        """
        bulk_submission_1-1-7.zip has an ODK directory from
        a device using ODK Collect 1.1.7.

        The metadata is in "odk/metadata/instances.db".
        """

        # import from sd card
        import_instances_from_zip(os.path.join(DB_FIXTURES_PATH, "bulk_submission_1-1-7.zip"), self.user)

        instance_count = Instance.objects.count()
        image_count = images_count()

        statii = sorted([x['status'] for x in Instance.objects.all().values('status')])

        # one of the imported surveys is "complete"
        self.assertEqual(statii[0], "complete")

        # one of the imported surveys is "incomplete"
        self.assertEqual(statii[1], "incomplete")

        #Images are not duplicated
        # TODO: Figure out how to get this test passing.
        self.assertEqual(image_count, 2)

        # Instance count should have incremented
        # by 1 (or 2) based on the b1 & b2 data sets
        self.assertEqual(instance_count, 2)

