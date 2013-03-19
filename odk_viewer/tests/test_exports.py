from sys import stdout
import os
import datetime
import json
import StringIO
import csv
from time import sleep
from django.conf import settings
from main.tests.test_base import MainTestCase
from django.core.urlresolvers import reverse
from odk_viewer.xls_writer import XlsWriter
from odk_viewer.views import delete_export, export_list, create_export,\
    export_progress, export_download
from odk_viewer.models import Export, ParsedInstance
from utils.export_tools import generate_export, increment_index_in_filename
from odk_logger.models import Instance, XForm
from main.views import delete_data
from utils.logger_tools import inject_instanceid
from django.core.files.storage import get_storage_class
from odk_viewer.pandas_mongo_bridge import NoRecordsFoundError
from odk_viewer.tasks import create_xls_export
from xlrd import open_workbook


class TestExports(MainTestCase):
    def setUp(self):
        super(TestExports, self).setUp()
        self._submission_time='2013-02-18 15:54:01'

    def test_unique_xls_sheet_name(self):
        xls_writer = XlsWriter()
        xls_writer.add_sheet('section9_pit_latrine_with_slab_group')
        xls_writer.add_sheet('section9_pit_latrine_without_slab_group')
        # create a set of sheet names keys
        sheet_names_set = set(xls_writer._sheets.keys())
        self.assertEqual(len(sheet_names_set), 2)

    def test_csv_http_response(self):
        self._publish_transportation_form()
        survey = self.surveys[0]
        self._make_submission(
            os.path.join(
                self.this_directory, 'fixtures', 'transportation',
                'instances', survey, survey + '.xml'),
            forced_submission_time=self._submission_time)
        response = self.client.get(reverse('csv_export',
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
        # test csv though xls uses the same view
        url = reverse('csv_export',
            kwargs={
                'username': self.user.username,
                'id_string': self.xform.id_string
            }
        )
        self.response = self.client.get(url)
        self.assertEqual(self.response.status_code, 404)
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
        export = generate_export(Export.XLS_EXPORT, 'xls', self.user.username,
                                 self.xform.id_string)
        storage = get_storage_class()()
        self.assertTrue(storage.exists(export.filepath))
        # delete export object
        export.delete()
        self.assertFalse(storage.exists(export.filepath))

    def test_graceful_exit_on_export_delete_if_file_doesnt_exist(self):
        self._publish_transportation_form()
        self._submit_transport_instance()
        export = generate_export(Export.XLS_EXPORT, 'xls', self.user.username,
            self.xform.id_string)
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
        first_export = generate_export(Export.XLS_EXPORT, 'xls', self.user.username,
            self.xform.id_string)
        self.assertIsNotNone(first_export.pk)
        # create exports that exceed set limit
        for i in range(Export.MAX_EXPORTS):
            generate_export(Export.XLS_EXPORT, 'xls', self.user.username,
                self.xform.id_string)
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
        export = generate_export(Export.XLS_EXPORT, 'xls', self.user.username,
            self.xform.id_string)
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
            generate_export(Export.XLS_EXPORT, 'xls', self.user.username,
                self.xform.id_string)
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
        xls_export = generate_export(Export.XLS_EXPORT, 'xls', self.user.username,
            self.xform.id_string)
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
        export = generate_export(Export.XLS_EXPORT, 'xls', self.user.username,
            self.xform.id_string)
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
        export_2 = generate_export(Export.CSV_EXPORT, 'csv', self.user.username,
                                   self.xform.id_string)
        if export.created_on.timetuple() == export_2.created_on.timetuple():
            new_filename = increment_index_in_filename(filename)
            self.assertEqual(new_filename, export_2.filename)
        else:
            stdout.write("duplicate export filename test skipped because export times differ.")

    def test_export_download_url(self):
        self._publish_transportation_form()
        self._submit_transport_instance()
        export = generate_export(Export.CSV_EXPORT, 'csv', self.user.username,
                                 self.xform.id_string)
        csv_export_url = reverse(export_download, kwargs={
            "username": self.user.username,
            "id_string": self.xform.id_string,
            "export_type": Export.CSV_EXPORT,
            "filename": export.filename
        })
        response = self.client.get(csv_export_url)
        self.assertEqual(response.status_code, 200)
        # test xls
        export = generate_export(Export.XLS_EXPORT, 'xls', self.user.username,
            self.xform.id_string)
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
        export = generate_export(Export.CSV_EXPORT, 'csv', self.user.username,
                                 self.xform.id_string)
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
        params = {'id': instance_id}
        self.client.post(delete_url, params)
        count = ParsedInstance.query_mongo(
            self.user.username, self.xform.id_string, '{}', '[]', '{}',
            count=True)[0]['count']
        self.assertEqual(count, initial_count + 1)
        # create the export
        csv_export_url = reverse(
            'csv_export', kwargs={"username": self.user.username,
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
            'csv_export', kwargs={"username": self.user.username,
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
        self.assertContains(response, '#delete-1234"')
        self.assertNotContains(response, '#delete-1,234"')

    def test_export_progress_updates(self):
        """
        Test that after generate_export is called, we change out state to
        pending and after its complete, we change it to complete, if we fail
        between the two, updates, we have failed
        """
        self._publish_transportation_form()
        # generate an export that fails because of the NoRecordsFound exception
        export = Export.objects.create(xform=self.xform,
            export_type=Export.XLS_EXPORT)
        # check that progress url says pending
        progress_url = reverse(export_progress, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string,
            'export_type': 'xls'
        })
        params = {'export_ids': [export.id]}
        response = self.client.get(progress_url, params)
        status = json.loads(response.content)[0]
        self.assertEqual(status["complete"], False)
        self.assertEqual(status["filename"], None)

        try:
            create_xls_export(
                self.user.username,
                self.xform.id_string, export.id)
        except NoRecordsFoundError:
            pass
        # check that progress url says failed
        progress_url = reverse(export_progress, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string,
            'export_type': 'xls'
        })
        params = {'export_ids': [export.id]}
        response = self.client.get(progress_url, params)
        status = json.loads(response.content)[0]
        self.assertEqual(status["complete"], True)
        self.assertEqual(status["filename"], None)

        # make a submission and create a valid export
        self._submit_transport_instance()
        create_xls_export(
            self.user.username,
            self.xform.id_string, export.id)
        params = {'export_ids': [export.id]}
        response = self.client.get(progress_url, params)
        status = json.loads(response.content)[0]
        self.assertEqual(status["complete"], True)
        self.assertIsNotNone(status["filename"])

    def test_direct_export_returns_newset_export_if_not_updated_since(self):
        self._publish_transportation_form()
        self._submit_transport_instance()
        self.assertEqual(self.response.status_code, 201)
        self._submit_transport_instance_w_uuid("transport_2011-07-25_19-05-36")
        self.assertEqual(self.response.status_code, 201)

        initial_num_csv_exports = Export.objects.filter(
            xform=self.xform, export_type=Export.CSV_EXPORT).count()
        initial_num_xls_exports = Export.objects.filter(
            xform=self.xform, export_type=Export.XLS_EXPORT).count()
        # request a direct csv export
        csv_export_url = reverse('csv_export', kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })
        xls_export_url = reverse('xls_export', kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })
        response = self.client.get(csv_export_url)
        self.assertEqual(response.status_code, 200)
        # we should have initial_num_exports + 1 exports
        num_csv_exports = Export.objects.filter(
            xform=self.xform, export_type=Export.CSV_EXPORT).count()
        self.assertEqual(num_csv_exports, initial_num_csv_exports + 1)

        # request another export without changing the data
        response = self.client.get(csv_export_url)
        self.assertEqual(response.status_code, 200)
        # we should still only have a single export object
        num_csv_exports = Export.objects.filter(
            xform=self.xform, export_type=Export.CSV_EXPORT).count()
        self.assertEqual(num_csv_exports, initial_num_csv_exports + 1)

        # this should not affect a direct XLS export and XLS should still re-generate
        response = self.client.get(xls_export_url)
        self.assertEqual(response.status_code, 200)
        num_xls_exports = Export.objects.filter(
            xform=self.xform, export_type=Export.XLS_EXPORT).count()
        self.assertEqual(num_xls_exports, initial_num_xls_exports + 1)

        # make sure xls doesnt re-generate if data hasn't changed
        response = self.client.get(xls_export_url)
        self.assertEqual(response.status_code, 200)
        num_xls_exports = Export.objects.filter(
            xform=self.xform, export_type=Export.XLS_EXPORT).count()
        self.assertEqual(num_xls_exports, initial_num_xls_exports + 1)

        # check that data edits cause a re-generation
        self._submit_transport_instance_w_uuid(
            "transport_2011-07-25_19-05-36-edited")
        self.assertEqual(self.response.status_code, 201)
        self.client.get(csv_export_url)
        self.assertEqual(response.status_code, 200)
        # we should have an extra export now that the data has been updated
        num_csv_exports = Export.objects.filter(
            xform=self.xform, export_type=Export.CSV_EXPORT).count()
        self.assertEqual(num_csv_exports, initial_num_csv_exports + 2)

        # and when we delete
        delete_url = reverse(delete_data, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })
        instance = Instance.objects.latest('date_modified')
        response = self.client.post(delete_url, {'id': instance.id})
        self.assertEqual(response.status_code, 200)
        response = self.client.get(csv_export_url)
        self.assertEqual(response.status_code, 200)
        # we should have an extra export now that the data has been updated by the delete
        num_csv_exports = Export.objects.filter(
            xform=self.xform, export_type=Export.CSV_EXPORT).count()
        self.assertEqual(num_csv_exports, initial_num_csv_exports + 3)
       
    def _get_csv_data(self, filepath):
        storage = get_storage_class()()
        csv_file = storage.open(filepath)
        reader = csv.DictReader(csv_file)
        data = reader.next()
        csv_file.close()
        return data
        
    def _get_xls_data(self, filepath):
        storage = get_storage_class()()
        with storage.open(filepath) as f:
            workbook = open_workbook(file_contents=f.read())
        transportation_sheet = workbook.sheet_by_name("transportation")
        self.assertTrue(transportation_sheet.nrows > 1)
        headers = transportation_sheet.row_values(0)
        column1 = transportation_sheet.row_values(1)
        return dict(zip(headers, column1))
    
    def test_column_header_delimiter_export_option(self):
        self._publish_transportation_form()
        # survey 1 has ambulance and bicycle as values for
        # transport/available_transportation_types_to_referral_facility
        self._submit_transport_instance(survey_at=1)
        create_csv_export_url = reverse(create_export, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string,
            'export_type': 'csv'
        })
        default_params = {}
        custom_params = {
            'options[group_delimiter]': '.',
        }
        # test csv with default group delimiter
        response = self.client.post(create_csv_export_url, default_params)
        self.assertEqual(response.status_code, 302)
        export = Export.objects.filter(
            xform=self.xform, export_type='csv').latest('created_on')
        self.assertTrue(bool(export.filepath))
        data = self._get_csv_data(export.filepath)
        self.assertTrue(
            data.has_key(
                'transport/available_transportation_types_to_referral_facility/ambulance'))
        self.assertEqual(
            data['transport/available_transportation_types_to_referral_facility/ambulance'], 'True')

        # test csv with dot delimiter
        response = self.client.post(create_csv_export_url, custom_params)
        self.assertEqual(response.status_code, 302)
        export = Export.objects.filter(
            xform=self.xform, export_type='csv').latest('created_on')
        self.assertTrue(bool(export.filepath))
        data = self._get_csv_data(export.filepath)
        self.assertTrue(
            data.has_key(
                'transport.available_transportation_types_to_referral_facility.ambulance'))
        self.assertEqual(
            data['transport.available_transportation_types_to_referral_facility.ambulance'], 'True')

        # test xls with default group delimiter
        create_csv_export_url = reverse(create_export, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string,
            'export_type': 'xls'
        })
        response = self.client.post(create_csv_export_url, default_params)
        self.assertEqual(response.status_code, 302)
        export = Export.objects.filter(
            xform=self.xform, export_type='xls').latest('created_on')
        self.assertTrue(bool(export.filepath))
        data = self._get_xls_data(export.filepath)
        self.assertTrue(
            data.has_key("transport/available_transportation_types_to_referral_facility/ambulance"))
        # xlrd reader seems to convert bools into integers i.e. 0 or 1
        self.assertEqual(
            data["transport/available_transportation_types_to_referral_facility/ambulance"], 1)
            
        # test xls with dot delimiter
        response = self.client.post(create_csv_export_url, custom_params)
        self.assertEqual(response.status_code, 302)
        export = Export.objects.filter(
            xform=self.xform, export_type='xls').latest('created_on')
        self.assertTrue(bool(export.filepath))
        data = self._get_xls_data(export.filepath)
        self.assertTrue(
            data.has_key("transport.available_transportation_types_to_referral_facility.ambulance"))
        # xlrd reader seems to convert bools into integers i.e. 0 or 1
        self.assertEqual(
            data["transport.available_transportation_types_to_referral_facility.ambulance"], 1)
            
    def test_split_select_multiple_export_option(self):
        self._publish_transportation_form()
        self._submit_transport_instance(survey_at=1)
        create_csv_export_url = reverse(create_export, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string,
            'export_type': 'csv'
        })
        default_params = {}
        custom_params = {
            'options[dont_split_select_multiples]': 'yes'
        }
        # test csv with default split select multiples
        response = self.client.post(create_csv_export_url, default_params)
        self.assertEqual(response.status_code, 302)
        export = Export.objects.filter(
            xform=self.xform, export_type='csv').latest('created_on')
        self.assertTrue(bool(export.filepath))
        data = self._get_csv_data(export.filepath)
        # we should have transport/available_transportation_types_to_referral_facility/ambulance as a separate column
        self.assertTrue(
            data.has_key(
                'transport/available_transportation_types_to_referral_facility/ambulance'))
                
        # test csv without default split select multiples
        response = self.client.post(create_csv_export_url, custom_params)
        self.assertEqual(response.status_code, 302)
        export = Export.objects.filter(
            xform=self.xform, export_type='csv').latest('created_on')
        self.assertTrue(bool(export.filepath))
        data = self._get_csv_data(export.filepath)
        # transport/available_transportation_types_to_referral_facility/ambulance should not be in its own column
        self.assertFalse(
            data.has_key(
                'transport/available_transportation_types_to_referral_facility/ambulance'))
        # transport/available_transportation_types_to_referral_facility should be a column
        self.assertTrue(
            data.has_key(
                'transport/available_transportation_types_to_referral_facility'))
        # check that ambulance is one the values within the transport/available_transportation_types_to_referral_facility column
        self.assertTrue("ambulance" in data['transport/available_transportation_types_to_referral_facility'].split(" "))

        create_xls_export_url = reverse(create_export, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string,
            'export_type': 'xls'
        })
        # test xls with default split select multiples
        response = self.client.post(create_xls_export_url, default_params)
        self.assertEqual(response.status_code, 302)
        export = Export.objects.filter(
            xform=self.xform, export_type='xls').latest('created_on')
        self.assertTrue(bool(export.filepath))
        data = self._get_xls_data(export.filepath)
        # we should have transport/available_transportation_types_to_referral_facility/ambulance as a separate column
        self.assertTrue(
            data.has_key(
                'transport/available_transportation_types_to_referral_facility/ambulance'))

        # test xls without default split select multiples
        response = self.client.post(create_xls_export_url, custom_params)
        self.assertEqual(response.status_code, 302)
        export = Export.objects.filter(
            xform=self.xform, export_type='xls').latest('created_on')
        self.assertTrue(bool(export.filepath))
        data = self._get_xls_data(export.filepath)
        # transport/available_transportation_types_to_referral_facility/ambulance should NOT be in its own column
        self.assertFalse(
            data.has_key(
                'transport/available_transportation_types_to_referral_facility/ambulance'))
        # transport/available_transportation_types_to_referral_facility should be a column
        self.assertTrue(
            data.has_key(
                'transport/available_transportation_types_to_referral_facility'))
        # check that ambulance is one the values within the transport/available_transportation_types_to_referral_facility column
        self.assertTrue("ambulance" in data['transport/available_transportation_types_to_referral_facility'].split(" "))
