from test_base import MainTestCase
from main.views import show, form_photos
from django.core.urlresolvers import reverse
from odk_logger.models import XForm
from odk_logger.views import download_xlsform, download_jsonform, download_xform

class TestFormShow(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        self._create_user_and_login()
        self._publish_transportation_form_and_submit_instance()
        self.url = reverse(show, kwargs={
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

    def test_dl_xls_to_anon_if_public(self):
        self.xform.shared = True
        self.xform.save()
        response = self.anon.get(reverse(download_xlsform, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        }))
        self.assertEqual(response.status_code, 200)

    def test_dl_json_to_anon_if_public(self):
        self.xform.shared = True
        self.xform.save()
        response = self.anon.get(reverse(download_jsonform, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        }))
        self.assertEqual(response.status_code, 200)

    def test_dl_xform_to_anon_if_public(self):
        self.xform.shared = True
        self.xform.save()
        response = self.anon.get(reverse(download_xform, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        }))
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

    def test_show_add_supporting_docs_if_owner(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'Upload')

    def test_hide_add_supporting_docs_if_not_owner(self):
        self.xform.shared = True
        self.xform.save()
        response = self.anon.get(self.url)
        self.assertNotContains(response, 'Upload')

    def test_load_photo_page(self):
        response = self.client.get(reverse(form_photos, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string}))
        self.assertEqual(response.status_code, 200)

    def test_load_from_uuid(self):
        self.xform = XForm.objects.get(pk=self.xform.id)
        response = self.client.get(reverse(show, kwargs={
            'uuid': self.xform.uuid}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'],
                '%s%s' % (self.base_url, self.url))
