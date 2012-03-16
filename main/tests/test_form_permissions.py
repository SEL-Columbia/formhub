from test_base import MainTestCase
from test_process import TestSite
from django.core.urlresolvers import reverse
from odk_logger.models import XForm
from odk_viewer.views import map_view, survey_responses
from guardian.shortcuts import assign, remove_perm
from main.views import set_perm, show, edit
from main.models import MetaData

import os

class TestFormPermissions(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        self._create_user_and_login()
        self._publish_transportation_form()
        s = 'transport_2011-07-25_19-05-49'
        self._make_submission(os.path.join(self.this_directory, 'fixtures',
            'transportation', 'instances', s, s + '.xml'))
        self.submission = self.xform.surveys.reverse()[0]
        self.url = reverse(map_view, kwargs={'username': self.user.username,
            'id_string': self.xform.id_string})
        self.perm_url = reverse(set_perm, kwargs={
            'username': self.user.username, 'id_string': self.xform.id_string})
        self.edit_url = reverse(edit, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })
        self.show_url = reverse(show,
                    kwargs={'uuid': self.xform.uuid})
        self.show_normal_url = reverse(show, kwargs={
                'username': self.user.username,
                'id_string': self.xform.id_string
        })

    def test_set_permissions_for_user(self):
        self._create_user_and_login('alice')
        self.assertEqual(self.user.has_perm('change_xform', self.xform), False)
        assign('change_xform', self.user, self.xform)
        self.assertEqual(self.user.has_perm('change_xform', self.xform), True)
        xform = self.xform
        self._publish_transportation_form()
        self.assertNotEqual(xform, self.xform)
        self.assertEqual(self.user.has_perm('change_xform', self.xform), False)

    def test_allow_map(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_restrict_map_for_anon(self):
        response = self.anon.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_restrict_map_for_not_owner(self):
        self._create_user_and_login('alice')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_allow_map_if_shared(self):
        self.xform.shared_data = True
        self.xform.save()
        response = self.anon.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_allow_map_if_user_given_permission(self):
        self._create_user_and_login('alice')
        assign('change_xform', self.user, self.xform)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_disallow_map_if_user_permission_revoked(self):
        self._create_user_and_login('alice')
        assign('change_xform', self.user, self.xform)
        response = self.client.get(self.url)
        remove_perm('change_xform', self.user, self.xform)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_require_owner_to_add_perm(self):
        response = self.anon.post(self.perm_url)
        self.assertEqual(response.status_code, 302)

    def test_add_view_to_user(self):
        user = self._create_user('alice', 'alice')
        response = self.client.post(self.perm_url, {'for_user': user.username,
            'perm_type': 'view'})
        self.assertEqual(response.status_code, 302)
        alice = self._login('alice', 'alice')
        response = alice.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_add_edit_to_user(self):
        user = self._create_user('alice', 'alice')
        response = self.client.post(self.perm_url, {'for_user': user.username,
            'perm_type': 'view'})
        self.assertEqual(response.status_code, 302)
        alice = self._login('alice', 'alice')
        response = alice.get(self.show_url)
        self.assertNotContains(response, self.xform.id_string)
        self.assertContains(response, 'Submissions:')

    def test_add_edit_to_user(self):
        user = self._create_user('alice', 'alice')
        response = self.client.post(self.perm_url, {'for_user': user.username,
            'perm_type': 'edit'})
        self.assertEqual(response.status_code, 302)
        alice = self._login('alice', 'alice')
        response = alice.post(self.edit_url)
        self.assertEqual(response.status_code, 302)

    def test_add_edit_to_user(self):
        user = self._create_user('alice', 'alice')
        response = self.client.post(self.perm_url, {'for_user': user.username,
            'perm_type': 'edit'})
        self.assertEqual(response.status_code, 302)
        alice = self._login('alice', 'alice')
        response = alice.get(self.show_normal_url)
        self.assertContains(response, 'Form ID: %s' % self.xform.id_string)

    def test_public_with_link_to_share(self):
        response = self.client.post(self.perm_url, {'for_user': 'all',
            'perm_type': 'link'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(MetaData.public_link(self.xform), True)
        response = self.anon.get(self.show_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'],
                '%s%s' % (self.base_url, self.show_normal_url))

    def test_private_set_link_to_share_off(self):
        response = self.client.post(self.perm_url, {'for_user': 'all',
            'perm_type': 'link'})
        self.assertEqual(MetaData.public_link(self.xform), True)
        response = self.anon.get(self.show_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'],
                '%s%s' % (self.base_url, self.show_normal_url))
        response = self.client.post(self.perm_url, {'for_user': 'none',
            'perm_type': 'link'})
        self.assertEqual(MetaData.public_link(self.xform), False)
        response = self.anon.get(self.show_url)
        self.assertEqual(response.status_code, 302)
        # follow redirect
        response = self.anon.get(response['Location'])
        self.assertEqual(response.status_code, 302)
        self.assertNotEqual(response['Location'],
                '%s%s' % (self.base_url, self.show_normal_url))

    def test_public_with_link_to_share_toggle_on(self):
        response = self.client.post(self.perm_url, {'for_user': 'toggle',
            'perm_type': 'link'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(MetaData.public_link(self.xform), True)
        response = self.anon.get(self.show_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'],
                '%s%s' % (self.base_url, self.show_normal_url))
        response = self.anon.get(self.show_normal_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '/forms/%s' % self.xform.uuid)

    def test_private_set_link_to_share_toggle_off(self):
        response = self.client.post(self.perm_url, {'for_user': 'toggle',
            'perm_type': 'link'})
        self.assertEqual(MetaData.public_link(self.xform), True)
        response = self.anon.get(self.show_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'],
                '%s%s' % (self.base_url, self.show_normal_url))
        response = self.client.post(self.perm_url, {'for_user': 'none',
            'perm_type': 'link'})
        self.assertEqual(MetaData.public_link(self.xform), False)
        response = self.anon.get(self.show_url)
        # follow redirect
        response = self.anon.get(response['Location'])
        self.assertEqual(response.status_code, 302)
        self.assertNotEqual(response['Location'],
                '%s%s' % (self.base_url, self.show_normal_url))

    def test_public_with_link_to_share_toggle_on(self):
        response = self.client.post(self.perm_url, {'for_user': 'toggle',
            'perm_type': 'link'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(MetaData.public_link(self.xform), True)
        response = self.anon.get(self.show_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'],
                '%s%s' % (self.base_url, self.show_normal_url))
        response = self.anon.get(self.show_normal_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '/forms/%s' % self.xform.uuid)

    def test_private_set_link_to_share_toggle_off(self):
        response = self.client.post(self.perm_url, {'for_user': 'toggle',
            'perm_type': 'link'})
        self.assertEqual(MetaData.public_link(self.xform), True)
        response = self.anon.get(self.show_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'],
                '%s%s' % (self.base_url, self.show_normal_url))
        response = self.client.post(self.perm_url, {'for_user': 'none',
            'perm_type': 'link'})
        self.assertEqual(MetaData.public_link(self.xform), False)
        response = self.anon.get(self.show_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'],
                '%s%s' % (self.base_url, self.show_normal_url))
        # follow redirect
        response = self.anon.get(response['Location'])
        self.assertEqual(response.status_code, 302)
        self.assertNotEqual(response['Location'],
                '%s%s' % (self.base_url, self.show_normal_url))

    def test_public_with_link_to_share_toggle_on(self):
        response = self.client.post(self.perm_url, {'for_user': 'toggle',
            'perm_type': 'link'})
        response = self.anon.get(self.show_url)
        response = self.anon.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_show_list_of_users_shared_with(self):
        new_username = 'alice'
        user = self._create_user(new_username, 'alice')
        response = self.client.post(self.perm_url, {'for_user': user.username,
            'perm_type': 'view'})
        self.assertEqual(response.status_code, 302)
        response = self.client.get(self.show_normal_url)
        self.assertContains(response, new_username)

    def test_anon_uuid_get_survey(self):
        survey_url = reverse(survey_responses, kwargs={
                'instance_id': self.submission.pk })
        response = self.client.post(self.perm_url, {'for_user': 'toggle',
            'perm_type': 'link'})
        self.assertEqual(response.status_code, 302)
        response = self.anon.get(self.show_url)
        self.assertEqual(response.status_code, 302)
        response = self.anon.get(survey_url)
        self.assertEquals(response.status_code, 200)
