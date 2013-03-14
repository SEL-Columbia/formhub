from test_base import MainTestCase
from odk_viewer.views import zip_export, kml_export, export_download
from django.core.urlresolvers import reverse
from common_tags import MONGO_STRFTIME

import os
import time
import csv
import tempfile
from xlrd import open_workbook
from utils.user_auth import http_auth_string
from utils.export_tools import generate_export
from odk_viewer.models import Export

class TestFormExports(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        self._create_user_and_login()
        self._publish_transportation_form_and_submit_instance()
        self.csv_url = reverse('csv_export', kwargs={
                'username': self.user.username,
                'id_string': self.xform.id_string})
        self.xls_url = reverse('xls_export', kwargs={
                'username': self.user.username,
                'id_string': self.xform.id_string})

    def _num_rows(self, content, export_format):
        def xls_rows(f):
            return open_workbook(file_contents=f).sheets()[0].nrows
        def csv_rows(f):
            with tempfile.TemporaryFile() as tmp:
                tmp.write(f.encode('utf-8'))
                tmp.seek(0)
                return len([line for line in csv.reader(tmp)])
        num_rows_fn = {
            'xls': xls_rows,
            'csv': csv_rows,
        }
        return num_rows_fn[export_format](content)

    def test_csv_raw_export_name(self):
        response = self.client.get(self.csv_url + '?raw=1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Disposition'], 'attachment;')

    def _filter_export_test(self, url, export_format):
        """
        Test filter exports.  Use sleep to ensure we don't have unique seconds.
        Number of rows equals number of surveys plus 1, the header row.
        """
        time.sleep(1)
        # 1 survey exists before this time
        before_time = time.strftime('%Y-%m-%dT%H:%M:%S')
        time.sleep(1)
        s = self.surveys[1]
        self._make_submission(os.path.join(self.this_directory, 'fixtures',
                    'transportation', 'instances', s, s + '.xml'))
        time.sleep(1)
        # 2 surveys exist before this time
        after_time = time.strftime('%Y-%m-%dT%H:%M:%S')
        time.sleep(1)
        # 3 surveys exist in total
        s = self.surveys[2]
        self._make_submission(os.path.join(self.this_directory, 'fixtures',
                    'transportation', 'instances', s, s + '.xml'))
        # test restricting to before end time
        json = '{"_submission_time": {"$lte": "%s"}}' % before_time
        params= {'query': json}
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._num_rows(response.content, export_format), 2)
        # test restricting to after start time
        json = '{"_submission_time": {"$gte": "%s"}}' % before_time
        params= {'query': json}
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._num_rows(response.content, export_format), 3)
        # test no time restriction
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._num_rows(response.content, export_format), 4)
        # test restricting to between start time and end time
        json = '{"_submission_time": {"$gte": "%s", "$lte": "%s"}}' %\
            (before_time, after_time)
        params= {'query': json}
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._num_rows(response.content, export_format), 2)

    def test_filter_by_date_csv(self):
        self._filter_export_test(self.csv_url, 'csv')

    def test_filter_by_date_xls(self):
        self._filter_export_test(self.xls_url, 'xls')

    def test_restrict_csv_export_if_not_shared(self):
        response = self.anon.get(self.csv_url)
        self.assertEqual(response.status_code, 403)

    def test_xls_raw_export_name(self):
        response = self.client.get(self.xls_url + '?raw=1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Disposition'], 'attachment;')

    def test_restrict_xls_export_if_not_shared(self):
        response = self.anon.get(self.xls_url)
        self.assertEqual(response.status_code, 403)

    def test_zip_raw_export_name(self):
        url = reverse(zip_export, kwargs={'username': self.user.username,
                'id_string': self.xform.id_string})
        response = self.client.get(url + '?raw=1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Disposition'], 'attachment;')

    def test_restrict_zip_export_if_not_shared(self):
        url = reverse(zip_export, kwargs={'username': self.user.username,
                'id_string': self.xform.id_string})
        response = self.anon.get(url)
        self.assertEqual(response.status_code, 403)

    def test_restrict_kml_export_if_not_shared(self):
        url = reverse(kml_export, kwargs={'username': self.user.username,
                'id_string': self.xform.id_string})
        response = self.anon.get(url)
        self.assertEqual(response.status_code, 403)

    def test_allow_csv_export_if_shared(self):
        self.xform.shared_data = True
        self.xform.save()
        response = self.anon.get(self.csv_url)
        self.assertEqual(response.status_code, 200)

    def test_allow_xls_export_if_shared(self):
        self.xform.shared_data = True
        self.xform.save()
        response = self.anon.get(self.xls_url)
        self.assertEqual(response.status_code, 200)

    def test_allow_zip_export_if_shared(self):
        self.xform.shared_data = True
        self.xform.save()
        url = reverse(zip_export, kwargs={'username': self.user.username,
                'id_string': self.xform.id_string})
        response = self.anon.get(url)
        self.assertEqual(response.status_code, 200)

    def test_allow_kml_export_if_shared(self):
        self.xform.shared_data = True
        self.xform.save()
        url = reverse(kml_export, kwargs={'username': self.user.username,
                'id_string': self.xform.id_string})
        response = self.anon.get(url)
        self.assertEqual(response.status_code, 200)

    def test_allow_csv_export(self):
        response = self.client.get(self.csv_url)
        self.assertEqual(response.status_code, 200)

    def test_allow_xls_export(self):
        response = self.client.get(self.xls_url)
        self.assertEqual(response.status_code, 200)

    def test_allow_zip_export(self):
        url = reverse(zip_export, kwargs={'username': self.user.username,
                'id_string': self.xform.id_string})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_allow_kml_export(self):
        url = reverse(kml_export, kwargs={'username': self.user.username,
                'id_string': self.xform.id_string})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_allow_csv_export_for_basic_auth(self):
        extra = {
            'HTTP_AUTHORIZATION': http_auth_string(self.login_username,
                self.login_password)
        }
        response = self.anon.get(self.csv_url, **extra)
        self.assertEqual(response.status_code, 200)

    def test_allow_xls_export_for_basic_auth(self):
        extra = {
            'HTTP_AUTHORIZATION': http_auth_string(self.login_username,
                self.login_password)
        }
        response = self.anon.get(self.xls_url, **extra)
        self.assertEqual(response.status_code, 200)

    def test_allow_zip_export_for_basic_auth(self):
        extra = {
            'HTTP_AUTHORIZATION': http_auth_string(self.login_username,
                self.login_password)
        }
        url = reverse(zip_export, kwargs={'username': self.user.username,
                                          'id_string': self.xform.id_string})
        response = self.anon.get(url, **extra)
        self.assertEqual(response.status_code, 200)

    def test_allow_kml_export_for_basic_auth(self):
        extra = {
            'HTTP_AUTHORIZATION': http_auth_string(self.login_username,
                self.login_password)
        }
        url = reverse(kml_export, kwargs={'username': self.user.username,
                                          'id_string': self.xform.id_string})
        response = self.anon.get(url, **extra)
        self.assertEqual(response.status_code, 200)

    def test_allow_export_download_for_basic_auth(self):
        extra = {
            'HTTP_AUTHORIZATION': http_auth_string(self.login_username,
                self.login_password)
        }
        # create export
        export = generate_export(Export.CSV_EXPORT, 'csv', self.user.username,
                                 self.xform.id_string)
        self.assertTrue(isinstance(export, Export))
        url = reverse(export_download, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string,
            'export_type': export.export_type,
            'filename': export.filename
        })
        response = self.anon.get(url, **extra)
        self.assertEqual(response.status_code, 200)
