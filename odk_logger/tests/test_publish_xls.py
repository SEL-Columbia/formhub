import os
import codecs

from django.core.management import call_command
from main.tests.test_base import MainTestCase
from odk_logger.models.xform import XForm


class TestPublishXLS(MainTestCase):

    def test_publish_xls(self):
        xls_file_path = os.path.join(
            self.this_directory, "fixtures",
            "transportation", "transportation.xls")
        count = XForm.objects.count()
        call_command('publish_xls', xls_file_path, self.user.username)
        self.assertEqual(XForm.objects.count(), count + 1)

    def test_publish_xls_replacement(self):
        count = XForm.objects.count()
        xls_file_path = os.path.join(
            self.this_directory, "fixtures",
            "transportation", "transportation.xls")
        call_command('publish_xls', xls_file_path, self.user.username)
        self.assertEqual(XForm.objects.count(), count + 1)
        count = XForm.objects.count()
        xls_file_path = os.path.join(
            self.this_directory, "fixtures",
            "transportation", "transportation_updated.xls")
        # call command without replace param
        failed = False
        try:
            call_command('publish_xls', xls_file_path, self.user.username)
        except SystemExit:
            failed = True
        self.assertTrue(failed)
        # now we call the command with the replace param
        call_command(
            'publish_xls', xls_file_path, self.user.username, replace=True)
        # count should remain the same
        self.assertEqual(XForm.objects.count(), count)
        # check if the extra field has been added
        self.xform = XForm.objects.order_by('id').reverse()[0]
        data_dictionary = self.xform.data_dictionary()
        is_updated_form = len([e.name for e in data_dictionary.survey_elements
                               if e.name == u'preferred_means']) > 0
        self.assertTrue(is_updated_form)

    def test_line_break_in_variables(self):
        xls_file_path = os.path.join(
            self.this_directory, "fixtures", 'exp_line_break.xlsx')
        xml_file_path = os.path.join(
            self.this_directory, "fixtures", 'exp_line_break.xml')
        test_xml_file_path = os.path.join(
            self.this_directory, "fixtures", 'test_exp_line_break.xml')
        self._publish_xls_file(xls_file_path)
        xforms = XForm.objects.filter(id_string='exp_line_break')
        self.assertTrue(xforms.count() > 0)
        xform = xforms[0]
        xform.xml = xform.xml.replace(xform.uuid, '663123a849e54bffa8f9832ef016bfac')
        xform.save()
        f = codecs.open(test_xml_file_path, 'w', encoding="utf-8")
        f.write(xform.xml)
        f.close()
        with codecs.open(xml_file_path, 'rb', encoding="utf-8") as expected_file:
            with codecs.open(test_xml_file_path, 'rb', encoding="utf-8") as actual_file:
                self.assertMultiLineEqual(expected_file.read(), actual_file.read())
        os.remove(test_xml_file_path)
