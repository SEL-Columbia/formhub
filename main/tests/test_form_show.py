from test_base import MainTestCase
from test_process import TestSite
from main.models import UserProfile, MetaData
from main.views import show, edit
from django.core.urlresolvers import reverse
from odk_logger.models import XForm
from odk_viewer.views import csv_export, xls_export, zip_export, kml_export, map_view
import os

class TestFormShow(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        self._create_user_and_login()
        xls_path = os.path.join(self.this_directory, "fixtures",
                "transportation", "transportation.xls")
        response = self._publish_xls_file(xls_path)
        self.assertEqual(XForm.objects.count(), 1)
        s = 'transport_2011-07-25_19-05-49'
        self._make_submission(os.path.join(self.this_directory, 'fixtures',
                    'transportation', 'instances', s, s + '.xml'))
        self.xform = XForm.objects.all()[0]
        self.url = reverse(show, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })
        self.edit_url = reverse(edit, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })

    def test_show_form_name(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.xform.id_string)

    def test_hide_from_anon(self):
        response = self.anon.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_hide_from_not_user(self):
        self._create_user_and_login("jo")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_show_to_anon_if_public(self):
        self.xform.shared = True
        self.xform.save()
        response = self.anon.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_show_private_if_shared_but_not_data(self):
        self.xform.shared = True
        self.xform.save()
        response = self.anon.get(self.url)
        self.assertContains(response, 'PRIVATE')

    def test_show_link_if_shared_and_data(self):
        self.xform.shared = True
        self.xform.shared_data = True
        self.xform.save()
        response = self.anon.get(self.url)
        self.assertContains(response, '/%s/data.csv' % self.xform.id_string)

    def test_show_link_if_owner(self):
        response = self.client.get(self.url)
        self.assertContains(response, '/%s/data.csv' % self.xform.id_string)
        self.assertContains(response, '/%s/data.xls' % self.xform.id_string)
        self.assertContains(response, '%s/map' % self.xform.id_string)

    def test_user_sees_edit_btn(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'edit</a>')

    def test_user_sees_settings(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'Settings')

    def test_anon_no_edit_btn(self):
        self.xform.shared = True
        self.xform.save()
        response = self.anon.get(self.url)
        self.assertNotContains(response, 'edit</a>')

    def test_anon_no_toggle_data_share_btn(self):
        self.xform.shared = True
        self.xform.save()
        response = self.anon.get(self.url)
        self.assertNotContains(response, 'PUBLIC</a>')
        self.assertNotContains(response, 'PRIVATE</a>')

    def test_anon_no_edit_post(self):
        self.xform.shared = True
        self.xform.save()
        desc = 'Snooky'
        response = self.anon.post(self.edit_url, {'description': desc})
        self.assertNotEqual(XForm.objects.get(pk=self.xform.pk).description, desc)
        self.assertEqual(response.status_code, 302)

    def test_not_owner_no_edit_post(self):
        self.xform.shared = True
        self.xform.save()
        desc = 'Snooky'
        self._create_user_and_login("jo")
        response = self.client.post(self.edit_url, {'description': desc})
        self.assertEqual(response.status_code, 405)
        self.assertNotEqual(XForm.objects.get(pk=self.xform.pk).description, desc)

    def test_user_description_edit_updates(self):
        desc = 'Snooky'
        response = self.client.post(self.edit_url, {'description': desc})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(XForm.objects.get(pk=self.xform.pk).description, desc)

    def test_user_title_edit_updates(self):
        desc = 'Snooky'
        response = self.client.post(self.edit_url, {'title': desc})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(XForm.objects.get(pk=self.xform.pk).title, desc)

    def test_user_form_license_edit_updates(self):
        desc = 'Snooky'
        response = self.client.post(self.edit_url, {'form-license': desc})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(MetaData.form_license(self.xform).data_value, desc)

    def test_user_data_license_edit_updates(self):
        desc = 'Snooky'
        response = self.client.post(self.edit_url, {'data-license': desc})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(MetaData.data_license(self.xform).data_value, desc)

    def test_user_toggle_data_privacy(self):
        self.assertEqual(self.xform.shared, False)
        response = self.client.post(self.edit_url, {'toggle_shared': 'data'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(XForm.objects.get(pk=self.xform.pk).shared_data, True)

    def test_user_toggle_data_privacy_off(self):
        self.xform.shared_data = True
        self.xform.save()
        response = self.client.post(self.edit_url, {'toggle_shared': 'data'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(XForm.objects.get(pk=self.xform.pk).shared_data, False)

    def test_user_toggle_form_privacy(self):
        self.assertEqual(self.xform.shared, False)
        response = self.client.post(self.edit_url, {'toggle_shared': 'form'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(XForm.objects.get(pk=self.xform.pk).shared, True)

    def test_user_toggle_form_privacy_off(self):
        self.xform.shared = True
        self.xform.save()
        response = self.client.post(self.edit_url, {'toggle_shared': 'form'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(XForm.objects.get(pk=self.xform.pk).shared, False)

    def test_user_toggle_form_downloadable(self):
        self.xform.downloadable = False
        self.xform.save()
        self.assertEqual(self.xform.downloadable, False)
        response = self.client.post(self.edit_url, {'toggle_shared': 'active'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(XForm.objects.get(pk=self.xform.pk).downloadable, True)

    def test_user_toggle_form_downloadable_off(self):
        self.xform.downloadable = True
        self.xform.save()
        response = self.client.post(self.edit_url, {'toggle_shared': 'active'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(XForm.objects.get(pk=self.xform.pk).downloadable, False)

    def test_restrict_csv_export_if_not_shared(self):
        url = reverse(csv_export, kwargs={'username': self.user.username,
                'id_string': self.xform.id_string})
        response = self.anon.get(url)
        self.assertEqual(response.status_code, 405)

    def test_restrict_xls_export_if_not_shared(self):
        url = reverse(xls_export, kwargs={'username': self.user.username,
                'id_string': self.xform.id_string})
        response = self.anon.get(url)
        self.assertEqual(response.status_code, 405)

    def test_restrict_zip_export_if_not_shared(self):
        url = reverse(zip_export, kwargs={'username': self.user.username,
                'id_string': self.xform.id_string})
        response = self.anon.get(url)
        self.assertEqual(response.status_code, 405)

    def test_restrict_kml_export_if_not_shared(self):
        url = reverse(kml_export, kwargs={'username': self.user.username,
                'id_string': self.xform.id_string})
        response = self.anon.get(url)
        self.assertEqual(response.status_code, 405)

    def test_allow_csv_export_if_shared(self):
        self.xform.shared_data = True
        self.xform.save()
        url = reverse(csv_export, kwargs={'username': self.user.username,
                'id_string': self.xform.id_string})
        response = self.anon.get(url)
        self.assertEqual(response.status_code, 200)

    def test_allow_xls_export_if_shared(self):
        self.xform.shared_data = True
        self.xform.save()
        url = reverse(xls_export, kwargs={'username': self.user.username,
                'id_string': self.xform.id_string})
        response = self.anon.get(url)
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
        url = reverse(csv_export, kwargs={'username': self.user.username,
                'id_string': self.xform.id_string})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_allow_xls_export(self):
        url = reverse(xls_export, kwargs={'username': self.user.username,
                'id_string': self.xform.id_string})
        response = self.client.get(url)
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

    def test_allow_map(self):
        url = reverse(map_view, kwargs={'username': self.user.username,
                'id_string': self.xform.id_string})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_restrict_map(self):
        url = reverse(map_view, kwargs={'username': self.user.username,
                'id_string': self.xform.id_string})
        response = self.anon.get(url)
        self.assertEqual(response.status_code, 405)

    def test_allow_map_if_shared(self):
        self.xform.shared_data = True
        self.xform.save()
        url = reverse(map_view, kwargs={'username': self.user.username,
                'id_string': self.xform.id_string})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

