import os
from datetime import datetime
from django.conf import settings
from odk_logger.import_tools import django_file
from main.tests.test_base import MainTestCase
from odk_logger.import_tools import create_instance
from utils.backup_tools import _date_created_from_filename


class TestBackupTools(MainTestCase):
    def setUp(self):
        MainTestCase.setUp(self)
        self._publish_xls_file(
            os.path.join(
                settings.PROJECT_ROOT,
                "odk_logger", "fixtures", "test_forms", "tutorial.xls"))

    def test_date_created_override(self):
        """
        Test that passing a date_created_override when creating and instance will set our date as the date_created
        """
        xml_file_path = os.path.join(
            settings.PROJECT_ROOT, "odk_logger", "fixtures", "tutorial",
            "instances", "tutorial_2012-06-27_11-27-53.xml")
        xml_file = django_file(
            xml_file_path, field_name="xml_file", content_type="text/xml")
        media_files = []
        date_created = datetime.strptime("2013-01-01 12:00:00",
            "%Y-%m-%d %H:%M:%S")
        instance = create_instance(self.user.username, xml_file, media_files,
            date_created_override=date_created)
        self.assertIsNotNone(instance)
        self.assertEqual(instance.date_created, date_created)

    def test_date_created_from_filename(self):
        date_str = "2012-01-02-12-35-48"
        date_created = datetime.strptime(date_str, "%Y-%m-%d-%H-%M-%S")
        filename = "%s.xml" % date_str
        generated_date_created = _date_created_from_filename(filename)
        self.assertEqual(generated_date_created, date_created)
        # test a filename with an index suffix
        filename = "%s-%d.xml" % (date_str, 1)
        generated_date_created = _date_created_from_filename(filename)
        self.assertEqual(generated_date_created, date_created)