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
