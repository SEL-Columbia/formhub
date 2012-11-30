from django.conf import settings
from django.core.urlresolvers import reverse

from main.models import MetaData
from main.views import edit
from odk_logger.views import formList
from odk_logger.models import XForm
from test_base import MainTestCase


class TestCrowdforms(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        self._create_user_and_login()
        self._publish_transportation_form()

        # turn on crowd forms for this form
        self.xform.is_crowd_form = True
        self.xform.save()
        self.edit_url = reverse(edit, kwargs={
            'username': self.xform.user.username,
            'id_string': self.xform.id_string
        })
        self.alice = 'alice'
        self.crowdform_count = 0

    def _close_crowdform(self):
        self.xform.is_crowd_form = False
        self.xform.save()

    def _add_crowdform(self):
        self._create_user_and_login(self.alice, self.alice)
        self.assertEqual(len(MetaData.crowdform_users(self.xform)),
                         self.crowdform_count)
        self.response = self.client.get(self.edit_url, {'crowdform': 'add'})
        self.crowdform_count += 1

    def test_owner_can_submit_form(self):
        self._make_submissions(add_uuid=True)
        self.assertEqual(self.response.status_code, 201)

    def test_other_user_can_submit_form(self):
        self._create_user_and_login(self.alice, self.alice)
        self._make_submissions(add_uuid=True)
        self.assertEqual(self.response.status_code, 201)

    def test_anonymous_can_view_crowdforms(self):
        self._logout()
        response = self.client.get(reverse(formList,
                                   kwargs={'username': 'crowdforms'}))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.xform.id_string in response.content)

    def test_anonymous_can_submit(self):
        self._logout()
        self._make_submissions('crowdforms', add_uuid=True)
        self.assertEqual(self.response.status_code, 201)

    def test_allow_owner_submit_to_closed_crowdform(self):
        self._close_crowdform()
        self._make_submissions(add_uuid=True)
        self.assertEqual(self.response.status_code, 201)

    def test_disallow_other_user_submit_to_closed_crowdform(self):
        self._close_crowdform()
        self._create_user_and_login('alice', 'alice')
        self._make_submissions(add_uuid=True, should_store=False)
        self.assertEqual(self.response.status_code, 405)

    def test_disallow_other_user_submit_to_closed_crowdform(self):
        self._close_crowdform()
        self._logout()
        self._make_submissions('crowdforms', add_uuid=True, should_store=False)
        self.assertEqual(self.response.status_code, 405)

    def test_user_add_crowdform(self):
        self._add_crowdform()
        self.assertEqual(self.response.status_code, 302)
        meta = MetaData.crowdform_users(self.xform)
        self.assertEqual(len(meta), 1)
        self.assertEqual(meta[0].data_value, self.alice)

    def test_disallow_access_to_closed_crowdform(self):
        self._close_crowdform()
        self._add_crowdform()
        self.assertEqual(self.response.status_code, 403)

    def test_user_can_view_added_crowdform(self):
        self._add_crowdform()
        response = self.client.get(reverse(formList,
                                   kwargs={'username': self.alice}))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.xform.id_string in response.content)

    def test_user_add_crowdform_duplicate_entry(self):
        self._add_crowdform()
        self.assertEqual(self.response.status_code, 302)
        meta = MetaData.crowdform_users(self.xform)
        self.assertEqual(len(meta), 1)
        self._add_crowdform()
        meta = MetaData.crowdform_users(self.xform)
        self.assertEqual(len(meta), 1)

    def test_user_delete_crowdform(self):
        self._add_crowdform()
        self.response = self.client.get(self.edit_url, {'crowdform': 'delete'})
        meta = MetaData.crowdform_users(self.xform)
        self.assertEqual(len(meta), 0)
        self.assertEqual(self.response.status_code, 302)

    def test_user_toggle_form_crowd_on(self):
        self.xform.shared = False
        self.xform.is_crowd_form = False
        self.xform.shared_data = False
        self.xform.save()
        response = self.client.post(self.edit_url, {'toggle_shared': 'crowd'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        xform = XForm.objects.get(pk=self.xform.pk)
        self.assertEqual(xform.shared, True)
        self.assertEqual(xform.shared_data, True)
        self.assertEqual(xform.is_crowd_form, True)

    def test_user_toggle_form_crowd_off(self):
        self.xform.shared = True
        self.xform.save()
        response = self.client.post(self.edit_url, {'toggle_shared': 'crowd'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        xform = XForm.objects.get(pk=self.xform.pk)
        self.assertEqual(xform.shared, True)
        self.assertEqual(xform.is_crowd_form, False)

    def test_crowdform_for_new_user(self):
        # initial
        meta = MetaData.crowdform_users(self.xform)
        self.assertEqual(len(meta), 0)

        #save settings to be restored later
        old_auto_add_cf = settings.AUTO_ADD_CROWDFORM
        old_default_cf = settings.DEFAULT_CROWDFORM

        # enable auto add crowdform
        settings.AUTO_ADD_CROWDFORM = True
        settings.DEFAULT_CROWDFORM = {
            'xform_username': self.user.username,
            'xform_id_string': self.xform.id_string}

        # register new user
        post_data = {
            'username': self.alice,
            'email': 'alice@columbia.edu',
            'password1': 'bobbob',
            'password2': 'bobbob',
            'name': 'Alice',
            'city': 'Ecila',
            'country': 'US',
            'organization': 'Alic Inc.',
            'home_page': 'alice.com',
            'twitter': 'alicerama'
        }
        url = '/accounts/register/'
        self.response = self.client.post(url, post_data)

        # check to ensure that crowd form was added
        meta = MetaData.crowdform_users(self.xform)
        self.assertEqual(len(meta), 1)
        self.assertEqual(meta[0].data_value, self.alice)

        # restore old settings
        settings.AUTO_ADD_CROWDFORM = old_auto_add_cf
        settings.DEFAULT_CROWDFORM = old_default_cf
