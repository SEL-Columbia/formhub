from django.core.urlresolvers import reverse
from main.tests.test_base import MainTestCase
from odk_viewer.views import instance
from guardian.shortcuts import assign_perm, remove_perm


class TestInstanceView(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        self._create_user_and_login()
        self._publish_transportation_form_and_submit_instance()
        self.url = reverse(instance, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })

    def test_instance_view(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_restrict_for_anon(self):
        response = self.anon.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_restrict_for_not_owner(self):
        self._create_user_and_login('alice')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_allow_if_shared(self):
        self.xform.shared_data = True
        self.xform.save()
        response = self.anon.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_allow_if_user_given_permission(self):
        self._create_user_and_login('alice')
        assign_perm('change_xform', self.user, self.xform)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_disallow_if_user_permission_revoked(self):
        self._create_user_and_login('alice')
        assign_perm('change_xform', self.user, self.xform)
        response = self.client.get(self.url)
        remove_perm('change_xform', self.user, self.xform)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)
