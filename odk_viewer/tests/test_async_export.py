import os
from celery import task
from django.conf import settings
from main.tests.test_base import MainTestCase
from odk_viewer.models.export import Export
from odk_viewer.tasks import create_xls_export


class TestAsyncExport(MainTestCase):
    def test_create_xls_export(self):
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
        # test async export
        result = create_xls_export.apply_async([], {
            'username': self.user.username,'id_string': self.xform.id_string})
        # TODO: how to test output when export is done
