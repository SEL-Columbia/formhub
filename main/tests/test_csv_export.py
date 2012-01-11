import os
from django.core.urlresolvers import reverse
from odk_viewer.views import csv_export
from odk_viewer.models import DataDictionary
from test_base import MainTestCase

class TestExport(MainTestCase):

    def setUp(self):
        self._create_user_and_login()
        self.fixtures = os.path.join(self.this_directory, 'fixtures', 'csv_export')
        path = os.path.join(self.fixtures, 'double_repeat.xls')
        self._publish_xls_file(path)
        path = os.path.join(self.fixtures, 'instance.xml')
        self._make_submission(path)
        self.maxDiff = None

    def test_csv_export(self):
        dd = DataDictionary.objects.all()[0]
        xpaths = [
            u'/double_repeat/bed_net[1]/member[1]/name',
            u'/double_repeat/bed_net[1]/member[2]/name',
            u'/double_repeat/bed_net[2]/member[1]/name',
            u'/double_repeat/bed_net[2]/member[2]/name',
            ]
        self.assertEquals(dd.xpaths(repeat_iterations=2), xpaths)
        url = reverse(csv_export, kwargs={'username': self.user.username, 'id_string': 'double_repeat'})
        response = self.client.get(url)
        with open(os.path.join(self.fixtures, 'export.csv')) as f:
            expected_content = f.read()
        self.assertEquals(response.content, expected_content)

