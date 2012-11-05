import os
from django.core.management.base import CommandError
from django.core.management import call_command
from main.tests.test_base import MainTestCase
from odk_logger.models.xform import XForm

class TestPublishXLS(MainTestCase):

    def test_publish_xls(self):
        xls_file_path = os.path.join(self.this_directory, "fixtures",
            "transportation", "transportation.xls")
        count = XForm.objects.count()
        call_command('publish_xls', xls_file_path, self.user.username)
        self.assertEqual(XForm.objects.count(), count + 1)

    def test_publish_xls_replacement(self):
        count = XForm.objects.count()
        xls_file_path = os.path.join(self.this_directory, "fixtures",
            "transportation", "transportation.xls")
        call_command('publish_xls', xls_file_path, self.user.username)
        self.assertEqual(XForm.objects.count(), count + 1)
        count = XForm.objects.count()
        xls_file_path = os.path.join(self.this_directory, "fixtures",
            "transportation", "transportation_updated.xls")
        # call command without replace param
        failed = False
        try:
            call_command('publish_xls', xls_file_path, self.user.username)
        except SystemExit:
            failed = True
        self.assertTrue(failed)
        # now we call the command with the replace param
        call_command('publish_xls', xls_file_path, self.user.username,
            replace=True)
        # count should remain the same
        self.assertEqual(XForm.objects.count(), count)
        # check if the extra field has been added
        self.xform = XForm.objects.order_by('id').reverse()[0]
        data_dictionary = self.xform.data_dictionary()
        is_updated_form = len([e.name for e in data_dictionary.survey_elements
                               if e.name == u'preferred_means']) > 0
        self.assertTrue(is_updated_form)
