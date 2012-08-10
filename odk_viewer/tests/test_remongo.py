from django.conf import settings
from main.tests.test_base import MainTestCase
from odk_viewer.models import ParsedInstance
from odk_viewer.management.commands.remongo import Command

class TestRemongo(MainTestCase):
    def test_remongo_in_batches(self):
      self._publish_transportation_form()
      # submit 5 instances
      for i in range(5):
          self._submit_transport_instance()
      self.assertEqual(ParsedInstance.objects.count(), 5)
      # clear mongo
      settings.MONGO_DB.instances.drop()
      c = Command()
      c.handle(batchsize=3)
      # mongo db should now have 5 records
      count = settings.MONGO_DB.instances.count()
      self.assertEqual(count, 5)

    def test_remongo_with_username_id_string(self):
        self._publish_transportation_form()
        # submit 5 instances
        for i in range(5):
            self._submit_transport_instance()
        # publish and submit for a different user
        self._logout()
        self._create_user_and_login("harry", "harry")
        self._publish_transportation_form()
        for i in range(4):
            self._submit_transport_instance()
        self.assertEqual(ParsedInstance.objects.count(), 9)
        # clear mongo
        settings.MONGO_DB.instances.drop()
        c = Command()
        c.handle(batchsize=3, username=self.user.username,
            id_string=self.xform.id_string)
        # mongo db should now have 5 records
        count = settings.MONGO_DB.instances.count()
        self.assertEqual(count, 4)
