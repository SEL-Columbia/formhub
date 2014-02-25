from test_base import MainTestCase
from main.views import edit
from django.core.urlresolvers import reverse
from odk_logger.models import XForm
from main.models import MetaData
from odk_logger.views import delete_xform

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

    def test_user_set_data_privacy(self):
        self.assertEqual(self.xform.shared, False)
        response = self.client.post(self.edit_url, {'settings_form': 'data', 'shared_data': 'on'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(XForm.objects.get(pk=self.xform.pk).shared_data, True)

    def test_user_unset_data_privacy_off(self):
        self.xform.shared_data = True
        self.xform.save()
        response = self.client.post(self.edit_url, {'settings_form': 'data', 'shared': 'on'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(XForm.objects.get(pk=self.xform.pk).shared_data, False)
        self.assertEqual(XForm.objects.get(pk=self.xform.pk).shared, True)   # does not clear other flag

    def test_user_set_form_privacy(self):
        self.assertEqual(self.xform.shared, False)
        response = self.client.post(self.edit_url, {'settings_form': 'form', 'shared': 'on'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(XForm.objects.get(pk=self.xform.pk).shared, True)

    def test_user_unset_form_privacy_off(self):
        self.xform.shared = True
        self.xform.save()
        response = self.client.post(self.edit_url, {'settings_form': 'form', 'shared_data': 'on'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(XForm.objects.get(pk=self.xform.pk).shared, False)
        self.assertEqual(XForm.objects.get(pk=self.xform.pk).shared_data, True)   # does not clear other flag

    def test_user_set_form_form_active(self):
        self.xform.form_active = False
        self.xform.save()
        self.assertEqual(self.xform.form_active, False)
        response = self.client.post(self.edit_url, {'settings_form': 'active', 'form_active': 'on'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(XForm.objects.get(pk=self.xform.pk).form_active, True)

    def test_user_unset_form_form_active_off(self):
        self.xform.form_active = True
        self.xform.save()
        response = self.client.post(self.edit_url, {'settings_form': 'active'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(XForm.objects.get(pk=self.xform.pk).form_active, False)

    def test_user_set_form_crowd_form(self):
        self.xform.shared = self.xform.shared_data = self.xform.is_crowd_form = False
        self.xform.save()
        self.assertEqual(self.xform.is_crowd_form, False)
        self.assertEqual(self.xform.shared, False)
        response = self.client.post(self.edit_url, {'settings_form': 'active', 'is_crowd_form': 'on'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(XForm.objects.get(pk=self.xform.pk).is_crowd_form, True)
        self.assertEqual(XForm.objects.get(pk=self.xform.pk).shared, True)       # setting crowd_form also sets shared
        self.assertEqual(XForm.objects.get(pk=self.xform.pk).shared_data, True)

    def test_user_unset_form_crowd_form_off(self):
        self.xform.crowd_form = True
        self.xform.save()
        response = self.client.post(self.edit_url, {'settings_form': 'active', 'shared': 'on'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(XForm.objects.get(pk=self.xform.pk).is_crowd_form, False)
        self.assertEqual(XForm.objects.get(pk=self.xform.pk).shared, True)   # does not clear other flag

    def test_delete_404(self):
        bad_delete_url = reverse(delete_xform, kwargs={
            'username': self.user.username,
            'id_string': 'non_existent_id_string'
        })
        response = self.client.post(bad_delete_url)
        self.assertEqual(response.status_code, 404)
