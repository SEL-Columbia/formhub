from test_base import MainTestCase
from odk_viewer.views import csv_export, xls_export, zip_export, kml_export
from django.core.urlresolvers import reverse

import time
import csv
import tempfile
from xlrd import open_workbook

class TestFormExports(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        self._create_user_and_login()
        self._publish_transportation_form_and_submit_instance()
        self.csv_url = reverse(csv_export, kwargs={
                'username': self.user.username,
                'id_string': self.xform.id_string})
        self.xls_url = reverse(xls_export, kwargs={
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
        before_time = time.strftime('%Y_%m_%d_%H_%M_%S')
        time.sleep(1)
        self._make_submissions()
        time.sleep(1)
        # 5 surveys exist before this time
        after_time = time.strftime('%Y_%m_%d_%H_%M_%S')
        time.sleep(1)
        # 9 surveys exist in total
        self._make_submissions()
        # test restricting to before end time
        response = self.client.get(url + '?end=%s' % before_time)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._num_rows(response.content, export_format), 2)
        # test restricting to after start time
        response = self.client.get(url + '?start=%s' % before_time)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._num_rows(response.content, export_format), 9)
        # test no time restriction
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._num_rows(response.content, export_format), 10)
        # test restricting to between start time and end time
        response = self.client.get(url + '?start=%s&end=%s' % (before_time,
                    after_time))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._num_rows(response.content, export_format), 5)

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
