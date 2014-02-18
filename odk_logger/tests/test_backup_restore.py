import os

from onadata.apps.main.tests.test_base import TestBase
from onadata.libs.utils.backup_tools import (
    restore_backup_from_xml_file,
    restore_backup_from_path)
from onadata.apps.logger.models import Instance


class TestBackupRestore(TestBase):
    def setUp(self):
        super(TestBackupRestore, self).setUp()
        self._publish_transportation_form()

    def test_restore_from_xml_file(self):
        count_qs = Instance.objects.filter(xform=self.xform)
        count = count_qs.count()
        xml_file_path = os.path.join(
            self.this_directory,
            'fixtures',
            'transportation',
            'backup_restore',
            '2011', '07', '25',
            '2011-07-25-19-05-36.xml')
        num_restored = restore_backup_from_xml_file(
            xml_file_path,
            self.user.username)
        self.assertEqual(num_restored, 1)
        self.assertEqual(count_qs.count(), count + 1)

    def test_restore_backup_from_path(self):
        count_qs = Instance.objects.filter(xform=self.xform)
        count = count_qs.count()
        path = os.path.join(
            self.this_directory,
            'fixtures',
            'transportation',
            'backup_restore',)
        num_instances, num_restored = restore_backup_from_path(
            path,
            self.user.username,
            None)
        self.assertEqual(num_instances, 1)
        self.assertEqual(num_restored, 1)
        self.assertEqual(count_qs.count(), count + 1)