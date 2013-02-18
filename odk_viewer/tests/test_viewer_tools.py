from django.test.client import RequestFactory
from main.tests.test_base import MainTestCase
from utils.viewer_tools import export_def_from_filename, get_client_ip


class TestViewerTools(MainTestCase):
    def test_export_def_from_filename(self):
        filename = "path/filename.xlsx"
        ext, mime_type = export_def_from_filename(filename)
        self.assertEqual(ext, 'xlsx')
        self.assertEqual(mime_type, 'vnd.openxmlformats')

    def test_get_client_ip(self):
        request = RequestFactory().get("/")
        client_ip = get_client_ip(request)
        self.assertIsNotNone(client_ip)
        # will this always be 127.0.0.1
        self.assertEqual(client_ip, "127.0.0.1")