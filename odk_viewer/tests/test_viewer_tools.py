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

    def test_delete_file_on_export_delete(self):
        self._publish_transportation_form()
        self._submit_transport_instance()
        xls_filename = create_xls_export(
            self.user.username, self.xform.id_string)
        export = Export.objects.all().reverse()[0]
        self.assertTrue(os.path.exists(
            os.path.join(
                settings.MEDIA_ROOT,
                export.filepath
            )
        ))
        # delete export object
        export.delete()
        self.assertFalse(os.path.exists(
            os.path.join(
                settings.MEDIA_ROOT,
                export.filepath
            )
        ))
