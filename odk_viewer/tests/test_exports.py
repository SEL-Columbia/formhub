import os
import datetime
import json
from django.conf import settings
from main.tests.test_base import MainTestCase
from django.core.urlresolvers import reverse
from odk_viewer.tasks import create_xls_export
from odk_viewer.xls_writer import XlsWriter
from odk_viewer.views import csv_export, xls_export, delete_export,\
    export_list, create_export, export_progress
from odk_viewer.models import Export
from utils.export_tools import generate_export

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
        export = generate_export(Export.XLS_EXPORT, 'xls', self.user.username,
            self.xform.id_string)
        self.assertTrue(os.path.exists(os.path.join(settings.MEDIA_ROOT,
            export.filepath)))
        path, ext = os.path.splitext(export.filename)
        self.assertEqual(ext, '.xls')

        # test csv
        export = generate_export(Export.CSV_EXPORT, 'csv', self.user.username,
            self.xform.id_string)
        self.assertTrue(os.path.exists(os.path.join(settings.MEDIA_ROOT,
            export.filepath)))
        path, ext = os.path.splitext(export.filename)
        self.assertEqual(ext, '.csv')

        # test flat csv
        export = generate_export(Export.FLAT_CSV_EXPORT, 'csv', self.user.username,
            self.xform.id_string)
        self.assertTrue(os.path.exists(os.path.join(settings.MEDIA_ROOT,
            export.filepath)))
        path, ext = os.path.splitext(export.filename)
        self.assertEqual(ext, '.csv')

        # test xls with existing export_id
        existing_export = Export.objects.create(xform=self.xform,
            export_type=Export.XLS_EXPORT)
        export = generate_export(Export.XLS_EXPORT, 'xls', self.user.username,
            self.xform.id_string, existing_export.id)
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

    def test_create_export_url(self):
        self._publish_transportation_form()
        self._submit_transport_instance()
        num_exports = Export.objects.count()
        # create export
        create_export_url = reverse(create_export, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string,
            'export_type': Export.XLS_EXPORT
        })
        response = self.client.post(create_export_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Export.objects.count(), num_exports + 1)

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

    def test_export_progress_output(self):
        self._publish_transportation_form()
        self._submit_transport_instance()
        # create exports
        for i in range(2):
            create_xls_export(
                self.user.username, self.xform.id_string)
        self.assertEqual(Export.objects.count(), 2)
        # progress for multiple exports
        progress_url = reverse(export_progress, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string,
            'export_type': 'xls'
        })
        get_data = {'export_ids': [e.id for e in Export.objects.all()]}
        response = self.client.get(progress_url, get_data)
        content = json.loads(response.content)
        self.assertEqual(len(content), 2)
        self.assertEqual(sorted(['url', 'export_id', 'complete', 'filename']),
            sorted(content[0].keys()))

    def test_auto_export_if_none_exists(self):
        self._publish_transportation_form()
        self._submit_transport_instance()
        # get export list url
        num_exports = Export.objects.count()
        export_list_url = reverse(export_list, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string,
            'export_type': Export.XLS_EXPORT
        })
        response = self.client.get(export_list_url)
        self.assertEqual(Export.objects.count(), num_exports + 1)

    def test_dont_auto_export_if_exports_exist(self):
        self._publish_transportation_form()
        self._submit_transport_instance()
        # create export
        create_export_url = reverse(create_export, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string,
            'export_type': Export.XLS_EXPORT
        })
        response = self.client.post(create_export_url)
        num_exports = Export.objects.count()
        export_list_url = reverse(export_list, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string,
            'export_type': Export.XLS_EXPORT
        })
        response = self.client.get(export_list_url)
        self.assertEqual(Export.objects.count(), num_exports)

    def test_last_submission_time_on_export(self):
        self._publish_transportation_form()
        self._submit_transport_instance()
        # create export
        export = create_xls_export(
            self.user.username, self.xform.id_string)
        num_exports = Export.objects.count()
        # check that our function knows there are no more submissions
        self.assertFalse(Export.exports_outdated(xform=self.xform))
        # force new  last submission date on xform
        last_submission = self.xform.surveys.order_by('-date_created')[0]
        last_submission.date_created += datetime.timedelta(hours=1)
        last_submission.save()
        # check that our function knows data has changed
        self.assertTrue(Export.exports_outdated(xform=self.xform))
        # check that requesting list url will generate a new export
        export_list_url = reverse(export_list, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string,
            'export_type': Export.XLS_EXPORT
        })
        response = self.client.get(export_list_url)
        self.assertEqual(Export.objects.count(), num_exports + 1)

    def test_last_submission_time_empty(self):
        self._publish_transportation_form()
        self._submit_transport_instance()
        # create export
        export = create_xls_export(
            self.user.username, self.xform.id_string)
        # set time of last submission to None
        export.time_of_last_submission = None
        export.save()
        self.assertTrue(Export.exports_outdated(xform=self.xform))

    def test_invalid_export_type(self):
        self._publish_transportation_form()
        self._submit_transport_instance()
        export_list_url = reverse(export_list, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string,
            'export_type': 'invalid'
        })
        response = self.client.get(export_list_url)
        self.assertEqual(response.status_code, 400)
        # test create url
        create_export_url = reverse(create_export, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string,
            'export_type': 'invalid'
        })
        response = self.client.post(create_export_url)
        self.assertEqual(response.status_code, 400)