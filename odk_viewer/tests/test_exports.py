from sys import stdout
import os
import datetime
import json
import StringIO
import csv
from django.conf import settings
from main.tests.test_base import MainTestCase
from django.core.urlresolvers import reverse
from odk_viewer.tasks import create_xls_export, create_csv_export
from odk_viewer.xls_writer import XlsWriter
from odk_viewer.views import csv_export, xls_export, delete_export,\
    export_list, create_export, export_progress, export_download
from odk_viewer.models import Export, ParsedInstance
from utils.export_tools import generate_export, increment_index_in_filename
from odk_logger.models import Instance
from main.views import delete_data
from utils.logger_tools import inject_instanceid
from django.core.files.storage import get_storage_class


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
        storage = get_storage_class()()
        # test xls
        export = generate_export(Export.XLS_EXPORT, 'xls', self.user.username,
            self.xform.id_string)
        self.assertTrue(storage.exists(export.filepath))
        path, ext = os.path.splitext(export.filename)
        self.assertEqual(ext, '.xls')

        # test csv
        export = generate_export(Export.CSV_EXPORT, 'csv', self.user.username,
            self.xform.id_string)
        self.assertTrue(storage.exists(export.filepath))
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
        storage = get_storage_class()()
        self.assertTrue(storage.exists(export.filepath))
        # delete export object
        export.delete()
        self.assertFalse(storage.exists(export.filepath))

    def test_graceful_exit_on_export_delete_if_file_doesnt_exist(self):
        self._publish_transportation_form()
        self._submit_transport_instance()
        export = create_xls_export(
            self.user.username, self.xform.id_string)
        storage = get_storage_class()()
        # delete file
        storage.delete(export.filepath)
        self.assertFalse(storage.exists(export.filepath))
        # clear filename, like it would be in an incomplete export
        export.filename = None
        export.filedir = None
        export.save()
        # delete export record, which should try to delete file as well
        delete_url = reverse(delete_export, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string,
            'export_type': 'xls'
        })
        post_data = {'export_id': export.id}
        response = self.client.post(delete_url, post_data)
        self.assertEqual(response.status_code, 302)

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
        xls_export = create_xls_export(
            self.user.username, self.xform.id_string)
        num_exports = Export.objects.filter(xform=self.xform,
            export_type=Export.XLS_EXPORT).count()
        # check that our function knows there are no more submissions
        self.assertFalse(Export.exports_outdated(xform=self.xform,
            export_type=Export.XLS_EXPORT))
        # force new  last submission date on xform
        last_submission = self.xform.surveys.order_by('-date_created')[0]
        last_submission.date_created += datetime.timedelta(hours=1)
        last_submission.save()
        # check that our function knows data has changed
        self.assertTrue(Export.exports_outdated(xform=self.xform,
            export_type=Export.XLS_EXPORT))
        # check that requesting list url will generate a new export
        export_list_url = reverse(export_list, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string,
            'export_type': Export.XLS_EXPORT
        })
        response = self.client.get(export_list_url)
        self.assertEqual(Export.objects.filter(xform=self.xform,
            export_type=Export.XLS_EXPORT).count(), num_exports + 1)
        # make sure another export type causes auto-generation
        num_exports = Export.objects.filter(xform=self.xform,
            export_type=Export.CSV_EXPORT).count()
        export_list_url = reverse(export_list, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string,
            'export_type': Export.CSV_EXPORT
        })
        response = self.client.get(export_list_url)
        self.assertEqual(Export.objects.filter(xform=self.xform,
            export_type=Export.CSV_EXPORT).count(), num_exports + 1)

    def test_last_submission_time_empty(self):
        self._publish_transportation_form()
        self._submit_transport_instance()
        # create export
        export = create_xls_export(
            self.user.username, self.xform.id_string)
        # set time of last submission to None
        export.time_of_last_submission = None
        export.save()
        self.assertTrue(Export.exports_outdated(xform=self.xform,
            export_type=Export.XLS_EXPORT))

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

    def test_add_index_to_filename(self):
        filename = "file_name-123f.txt"
        new_filename = increment_index_in_filename(filename)
        expected_filename = "file_name-123f-1.txt"
        self.assertEqual(new_filename, expected_filename)

        # test file that already has an index
        filename = "file_name-123.txt"
        new_filename = increment_index_in_filename(filename)
        expected_filename = "file_name-124.txt"
        self.assertEqual(new_filename, expected_filename)

    def test_duplicate_export_filename_is_renamed(self):
        self._publish_transportation_form()
        self._submit_transport_instance()
        # create an export object in the db
        # TODO: only works if the time we time we generate the basename is exact to the second with the time the 2nd export is created
        basename = "%s_%s" % (self.xform.id_string,
                              datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S"))
        filename = basename + ".csv"
        export = Export.objects.create(xform=self.xform,
            export_type=Export.CSV_EXPORT, filename=filename)
        # 2nd export
        export_2 = create_csv_export(username=self.user.username,
            id_string=self.xform.id_string)
        if export.created_on.timetuple() == export_2.created_on.timetuple():
            new_filename = increment_index_in_filename(filename)
            self.assertEqual(new_filename, export_2.filename)
        else:
            stdout.write("duplicate export filename test skipped because export times differ.")

    def test_export_download_url(self):
        self._publish_transportation_form()
        self._submit_transport_instance()
        export = create_csv_export(username=self.user.username,
            id_string=self.xform.id_string)
        csv_export_url = reverse(export_download, kwargs={
            "username": self.user.username,
            "id_string": self.xform.id_string,
            "export_type": Export.CSV_EXPORT,
            "filename": export.filename
        })
        response = self.client.get(csv_export_url)
        self.assertEqual(response.status_code, 200)
        # test xls
        export = create_xls_export(username=self.user.username,
            id_string=self.xform.id_string)
        xls_export_url = reverse(export_download, kwargs={
            "username": self.user.username,
            "id_string": self.xform.id_string,
            "export_type": Export.XLS_EXPORT,
            "filename": export.filename
        })
        response = self.client.get(xls_export_url)
        self.assertEqual(response.status_code, 200)

    def test_404_on_export_io_error(self):
        """
        Test that we return a 404 when the response_with_mimetype_and_name encounters an IOError
        """
        self._publish_transportation_form()
        self._submit_transport_instance()
        export = create_csv_export(username=self.user.username,
            id_string=self.xform.id_string)
        export_url = reverse(export_download, kwargs={
            "username": self.user.username,
            "id_string": self.xform.id_string,
            "export_type": Export.CSV_EXPORT,
            "filename": export.filename
        })
        # delete the export
        export.delete()
        # access the export
        response = self.client.get(export_url)
        self.assertEqual(response.status_code, 404)

    def test_deleted_submission_not_in_export(self):
        self._publish_transportation_form()
        initial_count = ParsedInstance.query_mongo(
            self.user.username, self.xform.id_string, '{}', '[]', '{}',
            count=True)[0]['count']
        self._submit_transport_instance(0)
        self._submit_transport_instance(1)
        count = ParsedInstance.query_mongo(
            self.user.username, self.xform.id_string, '{}', '[]', '{}',
            count=True)[0]['count']
        self.assertEqual(count, initial_count+2)
        # get id of second submission
        instance_id = Instance.objects.filter(
            xform=self.xform).order_by('id').reverse()[0].id
        delete_url = reverse(
            delete_data, kwargs={"username": self.user.username,
                                 "id_string": self.xform.id_string})
        self.client.post(delete_url, {"query": '{"_id": %d}' % instance_id})
        count = ParsedInstance.query_mongo(
            self.user.username, self.xform.id_string, '{}', '[]', '{}',
            count=True)[0]['count']
        self.assertEqual(count, initial_count+1)
        # create the export
        csv_export_url = reverse(
            csv_export, kwargs={"username": self.user.username,
                                "id_string":self.xform.id_string})
        response = self.client.get(csv_export_url)
        self.assertEqual(response.status_code, 200)
        f = StringIO.StringIO(response.content)
        csv_reader = csv.reader(f)
        num_rows = len([row for row in csv_reader])
        f.close()
        # number of rows == 2 i.e. initial_count + header plus one row
        self.assertEqual(num_rows, initial_count + 2)

    def test_edited_submissions_in_exports(self):
        self._publish_transportation_form()
        initial_count = ParsedInstance.query_mongo(
            self.user.username, self.xform.id_string, '{}', '[]', '{}',
            count=True)[0]['count']
        instance_name = 'transport_2011-07-25_19-05-36'
        path = os.path.join(
            'main', 'tests', 'fixtures', 'transportation', 'instances_w_uuid',
            instance_name, instance_name + '.xml')
        self._make_submission(path)
        count = ParsedInstance.query_mongo(
            self.user.username, self.xform.id_string, '{}', '[]', '{}',
            count=True)[0]['count']
        self.assertEqual(count, initial_count+1)
        instance = Instance.objects.filter(
            xform=self.xform).order_by('id').reverse()[0]
        # make edited submission - simulating what enketo would return
        instance_name = 'transport_2011-07-25_19-05-36-edited'
        path = os.path.join(
            'main', 'tests', 'fixtures', 'transportation', 'instances_w_uuid',
            instance_name, instance_name + '.xml')
        self._make_submission(path)
        count = ParsedInstance.query_mongo(
            self.user.username, self.xform.id_string, '{}', '[]', '{}',
            count=True)[0]['count']
        self.assertEqual(count, initial_count+1)
        # create the export
        csv_export_url = reverse(
            csv_export, kwargs={"username": self.user.username,
                                "id_string":self.xform.id_string})
        response = self.client.get(csv_export_url)
        self.assertEqual(response.status_code, 200)
        f = StringIO.StringIO(response.content)
        csv_reader = csv.DictReader(f)
        data = [row for row in csv_reader]
        f.close()
        num_rows = len(data)
        # number of rows == initial_count + 1
        self.assertEqual(num_rows, initial_count + 1)
        key ='transport/loop_over_transport_types_frequency/ambulance/frequency_to_referral_facility'
        self.assertEqual(data[initial_count][key], "monthly")

    def test_export_ids_dont_have_comma_separation(self):
        """
        It seems using {{ }} to output numbers greater than 1000 formats the
        number with a thousand separator
        """
        self._publish_transportation_form()
        self._submit_transport_instance()
        # create an in-complete export
        export = Export.objects.create(id=1234, xform=self.xform,
                              export_type=Export.XLS_EXPORT)
        self.assertEqual(export.pk, 1234)
        export_list_url = reverse(
            export_list, kwargs={
                "username": self.user.username,
                "id_string": self.xform.id_string,
                "export_type": Export.XLS_EXPORT
            })
        response = self.client.get(export_list_url)
        self.assertContains(response, '#delete-1234')
        self.assertNotContains(response, '#delete-1,234')
