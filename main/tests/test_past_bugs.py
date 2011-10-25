from test_process import TestSite
from test_base import MainTestCase
from odk_logger.models import XForm
import os


class TestCSVExport(TestSite):
    """
    We had a problem when two users published the same form that the
    CSV export would break.
    """

    def test_process(self):
        TestSite.test_process(self)
        TestSite.test_process(self, "doug", "doug")


class TestInputs(MainTestCase):
    """
    This is where I'll input all files that proved problematic for
    users when uploading.
    """

    def test_uniqueness_of_group_names_enforced(self):
        pre_count = XForm.objects.count()
        with self.assertRaises(Exception):
            self._publish_xls_file('fixtures/group_names_must_be_unique.xls')
        self.assertEqual(XForm.objects.count(), pre_count)

    def test_mch(self):
        self._publish_xls_file('fixtures/bug_fixes/MCH_v1.xls')

    def test_erics_files(self):
        for name in ['battery_life.xls',
                     'enumerator_weekly.xls',
                     'Enumerator_Training_Practice_Survey.xls',]:
            self._publish_xls_file(os.path.join('fixtures', 'bug_fixes', name))
