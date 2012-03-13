from test_base import MainTestCase
from main.views import edit
from django.core.urlresolvers import reverse
from odk_logger.models import XForm
from main.models import MetaData

class TestFormEdit(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        self._create_user_and_login()
        self._publish_transportation_form_and_submit_instance()
        self.edit_url = reverse(edit, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })

    def test_anon_no_edit_post(self):
        self.xform.shared = True
        self.xform.save()
        desc = 'Snooky'
        response = self.anon.post(self.edit_url, {'description': desc},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertNotEqual(
            XForm.objects.get(pk=self.xform.pk).description, desc)
        self.assertEqual(response.status_code, 302)

    def test_not_owner_no_edit_post(self):
        self.xform.shared = True
        self.xform.save()
        desc = 'Snooky'
        self._create_user_and_login("jo")
        response = self.client.post(self.edit_url, {'description': desc},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 403)
        self.assertNotEqual(
            XForm.objects.get(pk=self.xform.pk).description, desc)

    def test_user_description_edit_updates(self):
        desc = 'Snooky'
        response = self.client.post(self.edit_url, {'description': desc},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(XForm.objects.get(pk=self.xform.pk).description, desc)

    def test_user_title_edit_updates(self):
        desc = 'Snooky'
        response = self.client.post(self.edit_url, {'title': desc},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(XForm.objects.get(pk=self.xform.pk).title, desc)

    def test_user_form_license_edit_updates(self):
        desc = 'Snooky'
        response = self.client.post(self.edit_url, {'form-license': desc},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(MetaData.form_license(self.xform).data_value, desc)

    def test_user_data_license_edit_updates(self):
        desc = 'Snooky'
        response = self.client.post(self.edit_url, {'data-license': desc},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(MetaData.data_license(self.xform).data_value, desc)

    def test_user_toggle_data_privacy(self):
        self.assertEqual(self.xform.shared, False)
        response = self.client.post(self.edit_url, {'toggle_shared': 'data'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(XForm.objects.get(pk=self.xform.pk).shared_data, True)

    def test_user_toggle_data_privacy_off(self):
        self.xform.shared_data = True
        self.xform.save()
        response = self.client.post(self.edit_url, {'toggle_shared': 'data'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(XForm.objects.get(pk=self.xform.pk).shared_data, False)

    def test_user_toggle_form_privacy(self):
        self.assertEqual(self.xform.shared, False)
        response = self.client.post(self.edit_url, {'toggle_shared': 'form'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(XForm.objects.get(pk=self.xform.pk).shared, True)

    def test_user_toggle_form_privacy_off(self):
        self.xform.shared = True
        self.xform.save()
        response = self.client.post(self.edit_url, {'toggle_shared': 'form'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(XForm.objects.get(pk=self.xform.pk).shared, False)

    def test_user_toggle_form_downloadable(self):
        self.xform.downloadable = False
        self.xform.save()
        self.assertEqual(self.xform.downloadable, False)
        response = self.client.post(self.edit_url, {'toggle_shared': 'active'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(XForm.objects.get(pk=self.xform.pk).downloadable, True)

    def test_user_toggle_form_downloadable_off(self):
        self.xform.downloadable = True
        self.xform.save()
        response = self.client.post(self.edit_url, {'toggle_shared': 'active'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(XForm.objects.get(pk=self.xform.pk).downloadable, False)
