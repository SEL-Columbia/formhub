import os
import csv
from StringIO import StringIO
from django.core.urlresolvers import reverse
from odk_logger.models.xform import XForm
from odk_viewer.models import DataDictionary
from test_base import MainTestCase

class TestExport(MainTestCase):

    def setUp(self):
        self._create_user_and_login()
        self.fixture_dir = os.path.join(self.this_directory, 'fixtures',
                'csv_export')
        self._submission_time='2013-02-18 15:54:01'

    def test_csv_export_output(self):
        path = os.path.join(self.fixture_dir, 'tutorial_w_repeats.xls')
        self._publish_xls_file_and_set_xform(path)
        path = os.path.join(self.fixture_dir, 'tutorial_w_repeats.xml')
        self._make_submission(
            path, forced_submission_time=self._submission_time)
        url = reverse('csv_export', kwargs={'username': self.user.username,
                                          'id_string': self.xform.id_string})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        with open(os.path.join(self.fixture_dir, 'tutorial_w_repeats.csv')) as f:
            expected_content = f.read()
        self.assertEquals(response.content, expected_content)

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
        url = reverse('csv_export', kwargs={'username': self.user.username,
                'id_string': 'double_repeat'})
        response = self.client.get(url)
        with open(os.path.join(self.fixture_dir, 'export.csv')) as f:
            expected_content = f.read()
        self.assertEquals(response.content, expected_content)

    def test_dotted_fields_csv_export_output(self):
        path = os.path.join(os.path.dirname(__file__), 'fixtures', 'userone',
                'userone_with_dot_name_fields.xls')
        self._publish_xls_file_and_set_xform(path)
        path = os.path.join(os.path.dirname(__file__), 'fixtures', 'userone',
                'userone_with_dot_name_fields.xml')
        self._make_submission(
            path, forced_submission_time=self._submission_time)
        url = reverse('csv_export', kwargs={'username': self.user.username,
                                          'id_string': self.xform.id_string})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        with open(os.path.join(os.path.dirname(__file__), 'fixtures', 'userone',
                    'userone_with_dot_name_fields.csv')) as f:
            expected_content = f.read()
        self.assertEquals(response.content, expected_content)
