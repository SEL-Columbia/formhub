import os
from main.tests.test_base import MainTestCase
from utils.viewer_tools import export_def_from_filename


class TestViewerTools(MainTestCase):
    def test_export_def_from_filename(self):
        filename = "path/filename.xlsx"
        ext, mime_type = export_def_from_filename(filename)
        self.assertEqual(ext, 'xlsx')
        self.assertEqual(mime_type, 'vnd.openxmlformats')
