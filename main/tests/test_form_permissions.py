from test_base import MainTestCase
from test_process import TestSite
from django.core.urlresolvers import reverse
from odk_logger.models import XForm
from odk_viewer.views import map_view
from guardian.shortcuts import assign, remove_perm
from main.views import set_perm, show

import os

class TestFormPermissions(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        self._create_user_and_login()
        self._publish_transporation_form()
        s = 'transport_2011-07-25_19-05-49'
        self._make_submission(os.path.join(self.this_directory, 'fixtures',
            'transportation', 'instances', s, s + '.xml'))
        self.url = reverse(map_view, kwargs={'username': self.user.username,
            'id_string': self.xform.id_string})
        self.perm_url = reverse(set_perm, kwargs={
            'username': self.user.username, 'id_string': self.xform.id_string})

    def test_set_permissions_for_user(self):
        self._create_user_and_login('alice')
        self.assertEqual(self.user.has_perm('change_xform', self.xform), False)
        assign('change_xform', self.user, self.xform)
        self.assertEqual(self.user.has_perm('change_xform', self.xform), True)
        xform = self.xform
        self._publish_transporation_form()
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
        self.assertEqual(response.status_code, 403)

    def test_add_view_to_user(self):
        user = self._create_user('alice', 'alice')
        response = self.client.post(self.perm_url, {'for_user': user.username,
            'perm_type': 'view'})
        self.assertEqual(response.status_code, 200)
        alice = self._login('alice', 'alice')
        response = alice.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_add_edit_to_user(self):
        user = self._create_user('alice', 'alice')
        response = self.client.post(self.perm_url, {'for_user': user.username,
            'perm_type': 'edit'})
        self.assertEqual(response.status_code, 200)
        alice = self._login('alice', 'alice')
        # TODO: test some feature edit URL
        response = alice.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_public_with_link_to_share(self):
        response = self.client.post(self.perm_url, {'for_user': 'all',
            'perm_type': 'link'})
        self.assertEqual(response.status_code, 200)
        response = self.anon.get(reverse(show,
                    kwargs={'uuid': self.xform.uuid}))
        self.assertEqual(response.status_code, 200)

    def test_private_set_link_to_share_off(self):
        response = self.client.post(self.perm_url, {'for_user': 'all',
            'perm_type': 'link'})
        response = self.anon.get(reverse(show,
                    kwargs={'uuid': self.xform.uuid}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(self.perm_url, {'for_user': 'none',
            'perm_type': 'link'})
        self.assertEqual(response.status_code, 403)
