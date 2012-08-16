import os
from main.tests.test_base import MainTestCase
from utils.viewer_tools import create_xls_export

class TestViewerTools(MainTestCase):
    def test_create_xls_export(self):
        self._publish_transportation_form()
        self._submit_transport_instance()
        xls_file_path = create_xls_export(self.user, self.xform)
        self.assertTrue(os.path.exists(xls_file_path))