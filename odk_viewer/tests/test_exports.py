import os
from main.tests.test_base import MainTestCase
from django.core.urlresolvers import reverse
from odk_logger.views import download_xlsform
from odk_viewer.xls_writer import XlsWriter
from odk_viewer.views import csv_export, xls_export

class TestExports(MainTestCase):
    def test_unique_xls_sheet_name(self):
        xls_writer = XlsWriter()
        xls_writer.add_sheet('section9_pit_latrine_with_slab_group')
        xls_writer.add_sheet('section9_pit_latrine_without_slab_group')
        # create a set of sheet names keys
        sheet_names_set = set(xls_writer._sheets.keys())
        self.assertEqual(len(sheet_names_set), 2)

    def test_csv_http_response(self):
        self._create_user_and_login()
        self._publish_transportation_form()
        self._submit_transport_instance()
        response = self.client.get(reverse(csv_export,
            kwargs={
                'username': self.user.username,
                'id_string': self.xform.id_string
            }))
        self.assertEqual(response.status_code, 200)
        test_file_path = os.path.join(os.path.dirname(__file__), '..',
            'fixtures', 'transportation.csv')
        with open(test_file_path, 'r') as test_file:
            self.assertEqual(response.content, test_file.read())
        print response.content
