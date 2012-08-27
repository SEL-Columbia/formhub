from datetime import datetime
from django.core.urlresolvers import reverse
from django.utils import simplejson
from odk_logger.models.instance import Instance

from test_base import MainTestCase
from main.views import delete_data
from odk_viewer.models.parsed_instance import ParsedInstance


class TestFormAPIDelete(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        self._create_user_and_login()
        self._publish_transportation_form_and_submit_instance()
        self.delete_url = reverse(delete_data, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })

    def test_anon_user(self):
        #Only authenticated user are allowed to access the url
        response = self.anon.get(self.delete_url, {},
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 403)

    def test_delete_shared(self):
        #Test if someone can delete a shared form
        self.xform.shared = True
        self.xform.save()
        self._create_user_and_login("jo")
        json = '{"transport/available_transportation_types_to_referral_facility":"none"}'
        data = {'query': json}
        response = self.client.get(self.delete_url, data)
        self.assertEqual(response.status_code, 403)

    def test_owner_can_delete(self):
        #Test if Form owner can delete
        #check record exist before delete and after delete
        json = '{"transport/available_transportation_types_to_referral_facility":"none"}'
        data = {'query': json}
        args = {'username': self.user.username, 'id_string':
                    self.xform.id_string, 'query': json, 'limit': 1, 'sort':
                        '{"_id":-1}', 'fields': '["_id","_uuid"]'}

        #check if record exist before delete
        before = ParsedInstance.query_mongo(**args)
        self.assertEqual(before.count(), 1)
        records = list(record for record in before)
        uuid = records[0]['_uuid']
        instance  = Instance.objects.get(uuid=uuid, xform=self.xform)
        self.assertEqual(instance.deleted_at, None)

        #Delete
        response = self.client.get(self.delete_url, data)
        self.assertEqual(response.status_code, 200)
        instance  = Instance.objects.get(uuid=uuid, xform=self.xform)
        self.assertNotEqual(instance.deleted_at, None)
        self.assertTrue(isinstance(instance.deleted_at, datetime))

        #check if it exist after delete
        after = ParsedInstance.query_mongo(**args)
        self.assertEqual(after.count(), 0)
