from datetime import datetime
from django.core.urlresolvers import reverse
from django.utils import simplejson
from odk_logger.models.instance import Instance

from test_base import MainTestCase
from main.views import delete_data
from odk_viewer.models.parsed_instance import ParsedInstance
import common_tags
import settings


class TestFormAPIDelete(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        self._create_user_and_login()
        self._publish_transportation_form_and_submit_instance()
        self.delete_url = reverse(delete_data, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })
        self.mongo_args = {
            'username': self.user.username, 'id_string': self.xform.id_string,
            'query': "{}", 'limit': 1,
            'sort': '{"_id":-1}', 'fields': '["_id","_uuid"]'}

    def _get_data(self):
        cursor = ParsedInstance.query_mongo(**self.mongo_args)
        records = list(record for record in cursor)
        return records

    def test_get_request_does_not_delete(self):
        # not allowed 405
        count = Instance.objects.filter(deleted_at=None).count()
        response = self.anon.get(self.delete_url)
        self.assertEqual(response.status_code, 405)
        self.assertEqual(
            Instance.objects.filter(deleted_at=None).count(), count)

    def test_anon_user_cant_delete(self):
        # Only authenticated user are allowed to access the url
        count = Instance.objects.filter(deleted_at=None).count()
        instance = Instance.objects.filter(
            xform=self.xform).latest('date_created')
        # delete
        params = {'id': instance.id}
        response = self.anon.post(self.delete_url, params)
        self.assertEqual(response.status_code, 302)
        self.assertIn("accounts/login/?next=", response["Location"])
        self.assertEqual(
            Instance.objects.filter(deleted_at=None).count(), count)

    def test_delete_shared(self):
        #Test if someone can delete data from a shared form
        self.xform.shared = True
        self.xform.save()
        self._create_user_and_login("jo")
        count = Instance.objects.filter(deleted_at=None).count()
        instance = Instance.objects.filter(
            xform=self.xform).latest('date_created')
        # delete
        params = {'id': instance.id}
        response = self.client.post(self.delete_url, params)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            Instance.objects.filter(deleted_at=None).count(), count)

    def test_owner_can_delete(self):
        #Test if Form owner can delete
        #check record exist before delete and after delete
        count = Instance.objects.filter(deleted_at=None).count()
        instance = Instance.objects.filter(
            xform=self.xform).latest('date_created')
        # delete
        params = {'id': instance.id}
        response = self.client.post(self.delete_url, params)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Instance.objects.filter(deleted_at=None).count(), count - 1)
        instance  = Instance.objects.get(id=instance.id)
        self.assertTrue(isinstance(instance.deleted_at, datetime))
        query = '{"_id": %s}' % instance.id
        self.mongo_args.update({"query": query})
        #check that query_mongo will not return the deleted record
        after = ParsedInstance.query_mongo(**self.mongo_args)
        self.assertEqual(len(after), count - 1)

    def test_delete_updates_mongo(self):
        count = Instance.objects.filter(
            xform=self.xform, deleted_at=None).count()
        instance = Instance.objects.filter(
            xform=self.xform).latest('date_created')
        # delete
        params = {'id': instance.id}
        response = self.client.post(self.delete_url, params)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Instance.objects.filter(
                xform=self.xform, deleted_at=None).count(), count - 1)
        # check that instance's deleted_at is set
        instance  = Instance.objects.get(id=instance.id)
        self.assertTrue(isinstance(instance.deleted_at, datetime))
        # check mongo record was marked as deleted
        cursor = settings.MONGO_DB.instances.find({common_tags.ID: instance.id})
        self.assertEqual(cursor.count(), 1)
        record = cursor.next()
        self.assertIsNotNone(record[common_tags.DELETEDAT])
