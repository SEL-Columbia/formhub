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

    def _publish_nested_repeats_form(self):
        xls_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../fixtures/nested_repeats/nested_repeats.xls"
        )
        count = XForm.objects.count()
        response = self._publish_xls_file(xls_file_path)
        self.assertEqual(XForm.objects.count(), count + 1)
        self.xform = XForm.objects.all().reverse()[0]
        self.survey_name = u"new_repeats"

    def _submit_nested_repeats_instance(self):
        xml_submission_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../fixtures/nested_repeats/instances/nested_repeats_01.xml"
        )
        self._make_submission(xml_submission_file_path)
        self.assertEqual(self.response.status_code, 201)

    def _xls_data_for_dataframe(self):
        xls_df_builder = XLSDataFrameBuilder(self.user.username, self.xform.id_string)
        cursor = xls_df_builder._query_mongo()
        return xls_df_builder._format_for_dataframe(cursor)

    def _csv_data_for_dataframe(self):
        csv_df_builder = CSVDataFrameBuilder(self.user.username, self.xform.id_string)
        cursor = csv_df_builder._query_mongo()
        return csv_df_builder._format_for_dataframe(cursor)

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
        data = self._xls_data_for_dataframe()
        self.assertEqual(len(data[self.survey_name]), 1)
        self.assertEqual(len(data[u"kids_details"]), 2)

    def test_xls_columns(self):
        """
        Test that our expected columns are in the data


        """
        self._publish_new_repeats_form()
        self._submit_new_repeats_instance()
        data = self._xls_data_for_dataframe()
        expected_default_columns = [u"gps", u"web_browsers/firefox", u"web_browsers/safari", u"web_browsers/ie",
                                    u"info/age", u"web_browsers/chrome", u"kids/has_kids",
                                    u"info/name"] + XLSDataFrameBuilder.EXTRA_COLUMNS
        default_columns = [k for k in data[self.survey_name][0]]
        self.assertEqual(sorted(expected_default_columns), sorted(default_columns))
        expected_kids_details_columns = [u"kids/kids_details/kids_name", u"kids/kids_details/kids_age"] \
          + XLSDataFrameBuilder.EXTRA_COLUMNS
        kids_details_columns = [k for k in data[u"kids_details"][0]]
        self.assertEqual(sorted(expected_kids_details_columns), sorted(kids_details_columns))

    def test_csv_columns(self):
        self._publish_nested_repeats_form()
        self._submit_nested_repeats_instance()
        dd = self.xform.data_dictionary()
        expected_columns = [u'info/name', u'info/age', u'kids/has_kids', u'kids/kids_details/kids_name',
                            u'kids/kids_details/kids_age', u'kids/kids_details[2]/kids_name',
                            u'kids/kids_details[2]/kids_age', u'kids/kids_details[3]/kids_name',
                            u'kids/kids_details[3]/kids_age', u'kids/kids_details[4]/kids_name',
                            u'kids/kids_details[4]/kids_age', u'gps', u'gps_latitude', u'gps_longitude',
                            u'gps_alt', u'gps_precision', u'web_browsers/firefox', u'web_browsers/chrome',
                            u'web_browsers/ie', u'web_browsers/safari', u'_xform_id_string',
                            u'_percentage_complete', u'_status', u'_id', u'_attachments', u'_potential_duplicates']
        columns = dd.get_keys()
        print "columns: %s\n" % columns
        self.assertEqual(sorted(expected_columns), sorted(columns))

    def test_format_mongo_data_for_csv_columns(self):
        self._publish_nested_repeats_form()
        self._submit_nested_repeats_instance()
        dd = self.xform.data_dictionary()
        columns = dd.get_keys()
        data = self._csv_data_for_dataframe()
        expected_data_0 = {u'gps': u'-1.2627557 36.7926442 0.0 30.0', u'kids/has_kids': u'1', u'_attachments': [],
                          u'info/age': u'80', u'_xform_id_string': u'new_repeat', u'_status': u'submitted_via_web',
                          u'kids/kids_details/kids_name': u'Abel', u'kids/kids_details/kids_age': u'50',
                          u'kids/kids_details[2]/kids_name': u'Cain', u'kids/kids_details[2]/kids_age': u'76',
                          u'web_browsers/chrome': u'TRUE', u'web_browsers/ie': u'TRUE',
                          u'web_browsers/safari': u'FALSE', u'web_browsers/firefox': u'FALSE', u'info/name': u'Adam'}
        self.assertEqual(sorted(expected_data_0.keys()), sorted(data[0].keys()))

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