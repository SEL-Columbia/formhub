import os
from django.conf import settings
from main.tests.test_base import MainTestCase
from odk_viewer.models.export import Export
from utils.viewer_tools import export_def_from_filename
from odk_viewer.tasks import create_xls_export


class TestViewerTools(MainTestCase):
    def test_export_def_from_filename(self):
        filename = "path/filename.xlsx"
        ext, mime_type = export_def_from_filename(filename)
        self.assertEqual(ext, 'xlsx')
        self.assertEqual(mime_type, 'vnd.openxmlformats')
