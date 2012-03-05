from test_base import MainTestCase
from odk_viewer.views import csv_export, xls_export, zip_export, kml_export
from django.core.urlresolvers import reverse

import time

class TestFormExports(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        self._create_user_and_login()
        self._publish_transporation_form_and_submit_instance()
        self.csv_url = reverse(csv_export, kwargs={
                'username': self.user.username,
                'id_string': self.xform.id_string})
        self.xls_url = reverse(xls_export, kwargs={
                'username': self.user.username,
                'id_string': self.xform.id_string})

    def test_csv_raw_export_name(self):
        response = self.client.get(self.csv_url + '?raw=1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Disposition'], 'attachment;')

    def _filter_export_test(self, url):
        first_time = time.strftime('%Y_%m_%d_%H_%M_%S')
        time.sleep(1)
        before_time = time.strftime('%Y_%m_%d_%H_%M_%S')
        response = self.client.get(url + '?end=%s' % before_time)
        self.assertEqual(response.status_code, 200)
        before_length = response['Content-Length']
        self._make_submissions()
        after_time = time.strftime('%Y_%m_%d_%H_%M_%S')
        response = self.client.get(url + '?start=%s' % before_time)
        after_length = response['Content-Length']
        response = self.client.get(url)
        full_length = response['Content-Length']
        self.assertEqual(after_length > before_length, True)
        self.assertEqual(full_length > after_length, True)
        response = self.client.get(url + '?end=%s' % first_time)
        before_length = response['Content-Length']
        self.assertEqual(after_length > before_length, True)
        self.assertEqual(full_length > before_length, True)

    def test_filter_by_date_csv(self):
        self._filter_export_test(self.csv_url)

    def test_filter_by_date_xls(self):
        self._filter_export_test(self.xls_url)

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
