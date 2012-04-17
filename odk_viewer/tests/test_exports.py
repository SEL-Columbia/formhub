from main.tests.test_base import MainTestCase
from django.core.urlresolvers import reverse
from odk_logger.views import download_xlsform
from odk_viewer.xls_writer import XlsWriter

class TestExports(MainTestCase):
    def test_unique_xls_sheet_name(self):
        xls_writer = XlsWriter()
        xls_writer.add_sheet('section9_pit_latrine_with_slab_group')
        xls_writer.add_sheet('section9_pit_latrine_without_slab_group')
        # create a set of sheet names keys
        sheet_names_set = set(xls_writer._sheets.keys())
        self.assertEqual(len(sheet_names_set), 2)
