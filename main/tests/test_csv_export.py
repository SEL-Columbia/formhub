import os
from django.core.files.storage import get_storage_class
from django.utils.dateparse import parse_datetime
from odk_viewer.models import DataDictionary, Export
from utils.export_tools import generate_export
from test_base import MainTestCase


class TestExport(MainTestCase):

    def setUp(self):
        self._create_user_and_login()
        self.fixture_dir = os.path.join(
            self.this_directory, 'fixtures', 'csv_export')
        self._submission_time = parse_datetime('2013-02-18 15:54:01Z')

    def test_csv_export_url(self):
        """TODO: test data csv export"""
        pass

    def test_csv_export_output(self):
        path = os.path.join(self.fixture_dir, 'tutorial_w_repeats.xls')
        self._publish_xls_file_and_set_xform(path)
        path = os.path.join(self.fixture_dir, 'tutorial_w_repeats.xml')
        self._make_submission(
            path, forced_submission_time=self._submission_time)
        # test csv
        export = generate_export(Export.CSV_EXPORT, 'csv', self.user.username,
                                 'tutorial_w_repeats')
        storage = get_storage_class()()
        self.assertTrue(storage.exists(export.filepath))
        path, ext = os.path.splitext(export.filename)
        self.assertEqual(ext, '.csv')
        with open(os.path.join(
                self.fixture_dir, 'tutorial_w_repeats.csv')) as f1:
            with storage.open(export.filepath) as f2:
                expected_content = f1.read()
                actual_content = f2.read()
                self.assertEquals(actual_content, expected_content)

    def test_csv_nested_repeat_output(self):
        path = os.path.join(self.fixture_dir, 'double_repeat.xls')
        self._publish_xls_file(path)
        path = os.path.join(self.fixture_dir, 'instance.xml')
        self._make_submission(
            path, forced_submission_time=self._submission_time)
        self.maxDiff = None
        dd = DataDictionary.objects.all()[0]
        xpaths = [
            u'/double_repeat/bed_net[1]/member[1]/name',
            u'/double_repeat/bed_net[1]/member[2]/name',
            u'/double_repeat/bed_net[2]/member[1]/name',
            u'/double_repeat/bed_net[2]/member[2]/name',
            u'/double_repeat/meta/instanceID'
        ]
        self.assertEquals(dd.xpaths(repeat_iterations=2), xpaths)
        # test csv
        export = generate_export(Export.CSV_EXPORT, 'csv', self.user.username,
                                 'double_repeat')
        storage = get_storage_class()()
        self.assertTrue(storage.exists(export.filepath))
        path, ext = os.path.splitext(export.filename)
        self.assertEqual(ext, '.csv')
        with open(os.path.join(self.fixture_dir, 'export.csv')) as f1:
            with storage.open(export.filepath) as f2:
                expected_content = f1.read()
                actual_content = f2.read()
                self.assertEquals(actual_content, expected_content)

    def test_dotted_fields_csv_export_output(self):
        path = os.path.join(os.path.dirname(__file__), 'fixtures', 'userone',
                            'userone_with_dot_name_fields.xls')
        self._publish_xls_file_and_set_xform(path)
        path = os.path.join(os.path.dirname(__file__), 'fixtures', 'userone',
                            'userone_with_dot_name_fields.xml')
        self._make_submission(
            path, forced_submission_time=self._submission_time)
        # test csv
        export = generate_export(Export.CSV_EXPORT, 'csv', self.user.username,
                                 'userone')
        storage = get_storage_class()()
        self.assertTrue(storage.exists(export.filepath))
        path, ext = os.path.splitext(export.filename)
        self.assertEqual(ext, '.csv')
        with open(os.path.join(
                os.path.dirname(__file__), 'fixtures', 'userone',
                'userone_with_dot_name_fields.csv')) as f1:
            with storage.open(export.filepath) as f2:
                expected_content = f1.read()
                actual_content = f2.read()
                self.assertEquals(actual_content, expected_content)
