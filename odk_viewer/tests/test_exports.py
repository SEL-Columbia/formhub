import os
from django.conf import settings
from main.tests.test_base import MainTestCase
from django.core.urlresolvers import reverse
from odk_viewer.tasks import create_xls_export
from odk_viewer.xls_writer import XlsWriter
from odk_viewer.views import csv_export, xls_export, delete_export
from test_pandas_mongo_bridge import xls_filepath_from_fixture_name,\
    xml_inst_filepath_from_fixture_name
from odk_viewer.models.export import XLS_EXPORT, CSV_EXPORT, Export,\
    generate_export

class TestExports(MainTestCase):
    def setUp(self):
        super(TestExports, self).setUp()

    def test_unique_xls_sheet_name(self):
        xls_writer = XlsWriter()
        xls_writer.add_sheet('section9_pit_latrine_with_slab_group')
        xls_writer.add_sheet('section9_pit_latrine_without_slab_group')
        # create a set of sheet names keys
        sheet_names_set = set(xls_writer._sheets.keys())
        self.assertEqual(len(sheet_names_set), 2)

    def test_csv_http_response(self):
        self._publish_transportation_form_and_submit_instance()
        response = self.client.get(reverse(csv_export,
            kwargs={
                'username': self.user.username,
                'id_string': self.xform.id_string
            }))
        self.assertEqual(response.status_code, 200)
        test_file_path = os.path.join(os.path.dirname(__file__),
            'fixtures', 'transportation.csv')
        with open(test_file_path, 'r') as test_file:
            self.assertEqual(response.content, test_file.read())

    def test_responses_for_empty_exports(self):
        self._publish_transportation_form()
        # test csv
        url = reverse(csv_export,
            kwargs={
                'username': self.user.username,
                'id_string': self.xform.id_string
            }
        )
        self.response = self.client.get(url)
        self.assertEqual(self.response.status_code, 200)
        self.assertIn('text/html', self.response['content-type'])
        # test xls
        url = reverse(xls_export,
            kwargs={
                'username': self.user.username,
                'id_string': self.xform.id_string
            }
        )
        self.response = self.client.get(url)
        self.assertEqual(self.response.status_code, 200)
        # we a htl response when we have no records
        self.assertIn('text/html', self.response['content-type'])

    def test_create_export(self):
        self._publish_transportation_form_and_submit_instance()
        # test xls
        export = generate_export(XLS_EXPORT, 'xls', self.user.username, self.xform.id_string)
        self.assertTrue(os.path.exists(os.path.join(settings.MEDIA_ROOT, export.filepath)))
        path, ext = os.path.splitext(export.filename)
        self.assertEqual(ext, '.xls')

        # test csv
        export = generate_export(CSV_EXPORT, 'csv', self.user.username, self.xform.id_string)
        self.assertTrue(os.path.exists(os.path.join(settings.MEDIA_ROOT, export.filepath)))
        path, ext = os.path.splitext(export.filename)
        self.assertEqual(ext, '.csv')

        # test xls with existing export_id
        existing_export = Export.objects.create(xform=self.xform, export_type=XLS_EXPORT)
        export = generate_export(XLS_EXPORT, 'xls', self.user.username, self.xform.id_string, existing_export.id)
        self.assertEqual(existing_export.id, export.id)

    def test_delete_file_on_export_delete(self):
        self._publish_transportation_form()
        self._submit_transport_instance()
        export = create_xls_export(
            self.user.username, self.xform.id_string)
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

    def test_delete_oldest_export_on_limit(self):
        self._publish_transportation_form()
        self._submit_transport_instance()
        # create first export
        first_export = create_xls_export(
            self.user.username, self.xform.id_string)
        self.assertTrue(first_export.pk>0)
        # create exports that exceed set limit
        for i in range(Export.MAX_EXPORTS):
            create_xls_export(
                self.user.username, self.xform.id_string)
        # first export should be deleted
        exports = Export.objects.filter(id=first_export.id)
        self.assertEqual(len(exports), 0)

    def test_delete_export_url(self):
        self._publish_transportation_form()
        self._submit_transport_instance()
        # create export
        export = create_xls_export(
            self.user.username, self.xform.id_string)
        exports = Export.objects.filter(id=export.id)
        self.assertEqual(len(exports), 1)
        delete_url = reverse(delete_export, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string,
            'export_type': 'xls'
        })
        post_data = {'export_id': export.id}
        response = self.client.post(delete_url, post_data)
        self.assertEqual(response.status_code, 302)
        exports = Export.objects.filter(id=export.id)
        self.assertEqual(len(exports), 0)
