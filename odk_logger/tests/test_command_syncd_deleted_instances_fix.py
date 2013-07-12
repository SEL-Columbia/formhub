from datetime import datetime
from django.utils import timezone
from django.core.management import call_command
from main.tests.test_base import MainTestCase
from odk_logger.models import Instance


class CommandSyncDeletedTests(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        self._create_user_and_login()
        self._publish_transportation_form_and_submit_instance()

    def test_command(self):
        count = Instance.objects.filter(deleted_at=None).count()
        self.assertTrue(count > 0)
        deleted_at = timezone.now()
        deleted_at = datetime.strptime(
            deleted_at.strftime("%Y-%m-%dT%H:%M:%S"), "%Y-%m-%dT%H:%M:%S")
        deleted_at = timezone.make_aware(deleted_at, timezone.utc)
        instance = Instance.objects.filter(deleted_at=None)[0]
        instance.deleted_at = deleted_at
        instance.save()

        # ensure mongo has deleted_at by calling remongo
        call_command('remongo')

        # reset deleted_at to None
        instance.deleted_at = None
        instance.save()

        same_instance = Instance.objects.get(pk=instance.pk)
        self.assertIsNone(same_instance.deleted_at)

        # reset the deleted_at time from datetime in mongo
        call_command('sync_deleted_instances_fix')
        same_instance = Instance.objects.get(pk=instance.pk)

        # deleted_at should now have a datetime value
        self.assertIsNotNone(same_instance.deleted_at)
        self.assertTrue(isinstance(same_instance.deleted_at, datetime))
        self.assertEqual(same_instance.deleted_at, deleted_at)

    def test_command_on_inactive_form(self):
        count = Instance.objects.filter(deleted_at=None).count()
        self.assertTrue(count > 0)
        deleted_at = timezone.now()
        instance = Instance.objects.filter(deleted_at=None)[0]
        instance.deleted_at = deleted_at
        instance.save()

        # ensure mongo has deleted_at by calling remongo
        call_command('remongo')

        # reset deleted_at to None
        instance.deleted_at = None
        instance.save()

        # make xform inactive
        self.xform.downloadable = False
        self.xform.save()
        same_instance = Instance.objects.get(pk=instance.pk)
        self.assertIsNone(same_instance.deleted_at)

        # reset the deleted_at time from datetime in mongo
        call_command('sync_deleted_instances_fix')
        same_instance = Instance.objects.get(pk=instance.pk)

        # deleted_at should now have a datetime value
        self.assertIsNone(same_instance.deleted_at)
