import os
from odk_logger.models.xform import XForm
from main.tests.test_base import MainTestCase
from odk_viewer.pandas_mongo_bridge import *

class TestPandasMongoBridge(MainTestCase):
    def setUp(self):
        self._create_user_and_login()

    def _publish_new_repeats_form(self):
        xls_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../fixtures/new_repeats/new_repeats.xls"
        )
        count = XForm.objects.count()
        response = self._publish_xls_file(xls_file_path)
        self.assertEqual(XForm.objects.count(), count + 1)
        self.xform = XForm.objects.all().reverse()[0]
        self.survey_name = u"new_repeats"

    def _submit_new_repeats_instance(self):
        xml_submission_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../fixtures/new_repeats/instances/new_repeats_2012-07-05-14-33-53.xml"
        )
        self._make_submission(xml_submission_file_path)
        self.assertEqual(self.response.status_code, 201)

    def _query_mongo(self):
        xls_df_builder = XLSDataFrameBuilder(self.user.username, self.xform.id_string)
        cursor = xls_df_builder._query_mongo()
        return xls_df_builder._format_for_dataframe(cursor)

    def test_generated_sections(self):
        self._publish_new_repeats_form()
        self._submit_new_repeats_instance()
        xls_df_builder = XLSDataFrameBuilder(self.user.username, self.xform.id_string)
        expected_section_keys = [self.survey_name, u"kids_details"]
        section_keys = [s[u"name"] for s in xls_df_builder.sections]
        self.assertEqual(sorted(expected_section_keys), sorted(section_keys))

    def test_row_counts(self):
        """
        Test the number of rows in each sheet

        We expect a single row in the main new_repeats sheet and 2 rows in the kids details sheet one for each repeat
        """
        self._publish_new_repeats_form()
        self._submit_new_repeats_instance()
        data = self._query_mongo()
        self.assertEqual(len(data[self.survey_name]), 1)
        self.assertEqual(len(data[u"kids_details"]), 2)

    def test_xls_columns(self):
        """
        Test that our expected columns are in the data


        """
        self._publish_new_repeats_form()
        self._submit_new_repeats_instance()
        data = self._query_mongo()
        expected_default_columns = [u"gps", u"web_browsers/firefox", u"web_browsers/safari", u"web_browsers/ie",
                                    u"info/age", u"web_browsers/chrome", u"kids/has_kids",
                                    u"info/name"] + XLSDataFrameBuilder.EXTRA_COLUMNS
        default_columns = [k for k in data[self.survey_name][0]]
        self.assertEqual(sorted(expected_default_columns), sorted(default_columns))
        expected_kids_details_columns = [u"kids/kids_details/kids_name", u"kids/kids_details/kids_age"] \
          + XLSDataFrameBuilder.EXTRA_COLUMNS
        kids_details_columns = [k for k in data[u"kids_details"][0]]
        self.assertEqual(sorted(expected_kids_details_columns), sorted(kids_details_columns))

    def test_valid_sheet_name(self):
        sheet_names = ["sheet_1", "sheet_2"]
        desired_sheet_name = "sheet_3"
        expected_sheet_name = "sheet_3"
        generated_sheet_name = get_valid_sheet_name(desired_sheet_name, sheet_names)
        self.assertEqual(generated_sheet_name, expected_sheet_name)

    def test_invalid_sheet_name(self):
        sheet_names = ["sheet_1", "sheet_2"]
        desired_sheet_name = "sheet_3_with_more_than_max_expected_length"
        expected_sheet_name = "sheet_3_with_more_than_max_exp"
        generated_sheet_name = get_valid_sheet_name(desired_sheet_name, sheet_names)
        self.assertEqual(generated_sheet_name, expected_sheet_name)

    def test_duplicate_sheet_name(self):
        sheet_names = ["sheet_2_with_duplicate_sheet_n", "sheet_2_with_duplicate_sheet_1"]
        duplicate_sheet_name = "sheet_2_with_duplicate_sheet_n"
        expected_sheet_name  = "sheet_2_with_duplicate_sheet_2"
        generated_sheet_name = get_valid_sheet_name(duplicate_sheet_name, sheet_names)
        self.assertEqual(generated_sheet_name, expected_sheet_name)