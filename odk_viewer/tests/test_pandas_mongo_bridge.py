import os
from django.core.urlresolvers import reverse
from tempfile import NamedTemporaryFile
from odk_logger.models.xform import XForm
from main.tests.test_base import MainTestCase
from odk_logger.xform_instance_parser import xform_instance_to_dict
from odk_viewer.pandas_mongo_bridge import *
from odk_viewer.views import xls_export

def xls_filepath_from_fixture_name(fixture_name):
    """
    Return an xls file path at tests/fixtures/[fixture]/fixture.xls
    """
    #TODO: currently this only works for fixtures in this app because of __file__
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "fixtures", fixture_name, fixture_name + ".xls"
    )

def xml_inst_filepath_from_fixture_name(fixture_name, instance_name):
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "fixtures", fixture_name, "instances",
        fixture_name + "_" + instance_name + ".xml"
    )


class TestPandasMongoBridge(MainTestCase):
    def setUp(self):
        self._create_user_and_login()

    def _publish_xls_fixture_set_xform(self, fixture):
        """
        Publish an xls file at tests/fixtures/[fixture]/fixture.xls
        """
        xls_file_path = xls_filepath_from_fixture_name(fixture)
        count = XForm.objects.count()
        response = self._publish_xls_file(xls_file_path)
        self.assertEqual(XForm.objects.count(), count + 1)
        self.xform = XForm.objects.all().reverse()[0]

    def _submit_fixture_instance(self, fixture, instance):
        """
        Submit an instance at
        tests/fixtures/[fixture]/instances/[fixture]_[instance].xml
        """
        xml_submission_file_path = xml_inst_filepath_from_fixture_name(fixture,
            instance)
        self._make_submission(xml_submission_file_path)
        self.assertEqual(self.response.status_code, 201)

    def _publish_single_level_repeat_form(self):
        self._publish_xls_fixture_set_xform("new_repeats")
        self.survey_name = u"new_repeats"

    def _publish_nested_repeats_form(self):
        self._publish_xls_fixture_set_xform("nested_repeats")
        self.survey_name = u"nested_repeats"

    def _publish_grouped_gps_form(self):
        self._publish_xls_fixture_set_xform("grouped_gps")
        self.survey_name = u"grouped_gps"

    def _xls_data_for_dataframe(self):
        xls_df_builder = XLSDataFrameBuilder(self.user.username,
            self.xform.id_string)
        cursor = xls_df_builder._query_mongo()
        return xls_df_builder._format_for_dataframe(cursor)

    def _csv_data_for_dataframe(self):
        csv_df_builder = CSVDataFrameBuilder(self.user.username,
            self.xform.id_string)
        cursor = csv_df_builder._query_mongo()
        return csv_df_builder._format_for_dataframe(cursor)

    def test_generated_sections(self):
        self._publish_single_level_repeat_form()
        self._submit_fixture_instance("new_repeats", "01")
        xls_df_builder = XLSDataFrameBuilder(self.user.username,
            self.xform.id_string)
        expected_section_keys = [self.survey_name, u"kids_details"]
        section_keys = [s[u"name"] for s in xls_df_builder.sections]
        self.assertEqual(sorted(expected_section_keys), sorted(section_keys))

    def test_row_counts(self):
        """
        Test the number of rows in each sheet

        We expect a single row in the main new_repeats sheet and 2 rows in the
        kids details sheet one for each repeat
        """
        self._publish_single_level_repeat_form()
        self._submit_fixture_instance("new_repeats", "01")
        data = self._xls_data_for_dataframe()
        self.assertEqual(len(data[self.survey_name]), 1)
        self.assertEqual(len(data[u"kids_details"]), 2)

    def test_xls_columns(self):
        """
        Test that our expected columns are in the data
        """
        self._publish_single_level_repeat_form()
        self._submit_fixture_instance("new_repeats", "01")
        data = self._xls_data_for_dataframe()
        # columns in the default sheet
        expected_default_columns = [
            u"gps",
            u"_gps_latitude",
            u"_gps_longitude",
            u"_gps_altitude",
            u"_gps_precision",
            u"web_browsers/firefox",
            u"web_browsers/safari",
            u"web_browsers/ie",
            u"info/age",
            u"web_browsers/chrome",
            u"kids/has_kids",
            u"info/name"
        ] + XLSDataFrameBuilder.EXTRA_COLUMNS
        default_columns = [k for k in data[self.survey_name][0]]
        self.assertEqual(sorted(expected_default_columns),
            sorted(default_columns))

        # columns in the kids_details sheet
        expected_kids_details_columns = [u"kids/kids_details/kids_name",
            u"kids/kids_details/kids_age"] \
          + XLSDataFrameBuilder.EXTRA_COLUMNS
        kids_details_columns = [k for k in data[u"kids_details"][0]]
        self.assertEqual(sorted(expected_kids_details_columns),
            sorted(kids_details_columns))

    def test_xls_columns_for_gps_within_groups(self):
        """
        Test that a valid xpath is generated for extra gps fields that are NOT
        top level
        """
        self._publish_grouped_gps_form()
        self._submit_fixture_instance("grouped_gps", "01")
        data = self._xls_data_for_dataframe()
        # columns in the default sheet
        expected_default_columns = [
            u"gps_group/gps",
            u"gps_group/_gps_latitude",
            u"gps_group/_gps_longitude",
            u"gps_group/_gps_altitude",
            u"gps_group/_gps_precision",
            u"web_browsers/firefox",
            u"web_browsers/safari",
            u"web_browsers/ie",
            u"web_browsers/chrome",
        ] + XLSDataFrameBuilder.EXTRA_COLUMNS
        default_columns = [k for k in data[self.survey_name][0]]
        self.assertEqual(sorted(expected_default_columns),
            sorted(default_columns))

    def test_xlsx_output_when_data_exceeds_limits(self):
        self._publish_xls_fixture_set_xform("xlsx_output")
        self._submit_fixture_instance("xlsx_output", "01")
        xls_builder = XLSDataFrameBuilder(username=self.user.username,
                id_string=self.xform.id_string)
        self.assertEqual(xls_builder.exceeds_xls_limits, True)
        # test that the view returns an xlsx file instead
        url = reverse(xls_export,
            kwargs={
                'username': self.user.username,
                'id_string': self.xform.id_string
            })
        self.response = self.client.get(url)
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(self.response["content-type"],\
               'application/vnd.openxmlformats')

    def test_xlsx_export_for_repeats(self):
        """
        Make sure exports run fine when the xlsx file has multiple sheets
        """
        self._publish_xls_fixture_set_xform("new_repeats")
        self._submit_fixture_instance("new_repeats", "01")
        xls_builder = XLSDataFrameBuilder(username=self.user.username,
                id_string=self.xform.id_string)
        # test that the view returns an xlsx file instead
        url = reverse(xls_export,
            kwargs={
                'username': self.user.username,
                'id_string': self.xform.id_string
            }
        )
        params = {
            'xlsx': 'true' # force xlsx
        }
        self.response = self.client.get(url, params)
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(self.response["content-type"],\
               'application/vnd.openxmlformats')


    def test_csv_dataframe_export_to(self):
        self._publish_nested_repeats_form()
        self._submit_fixture_instance("nested_repeats", "01")
        self._submit_fixture_instance("nested_repeats", "02")
        csv_df_builder = CSVDataFrameBuilder(self.user.username,
            self.xform.id_string)
        temp_file = NamedTemporaryFile(suffix=".csv", delete=False)
        csv_df_builder.export_to(temp_file)
        csv_fixture_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "fixtures", "nested_repeats", "nested_repeats.csv"
        )
        temp_file.close()
        fixture, output = '', ''
        with open(csv_fixture_path) as f:
            fixture = f.read()
        with open(temp_file.name) as f:
            output = f.read()
        os.unlink(temp_file.name)
        self.assertEqual(fixture, output)

    def test_csv_columns_for_gps_within_groups(self):
        self._publish_grouped_gps_form()
        self._submit_fixture_instance("grouped_gps", "01")
        data = self._csv_data_for_dataframe()
        columns = data[0].keys()
        expected_columns = [
            u'gps_group/gps',
            u'gps_group/_gps_latitude',
            u'gps_group/_gps_longitude',
            u'gps_group/_gps_altitude',
            u'gps_group/_gps_precision',
            u'web_browsers/firefox',
            u'web_browsers/chrome',
            u'web_browsers/ie',
            u'web_browsers/safari',
        ] + AbstractDataFrameBuilder.INTERNAL_FIELDS
        self.maxDiff = None
        self.assertEqual(sorted(expected_columns), sorted(columns))

    def test_format_mongo_data_for_csv(self):
        self.maxDiff = None
        self._publish_single_level_repeat_form()
        self._submit_fixture_instance("new_repeats", "01")
        dd = self.xform.data_dictionary()
        columns = dd.get_keys()
        data_0 = self._csv_data_for_dataframe()[0]
        # remove AbstractDataFrameBuilder.INTERNAL_FIELDS
        for key in AbstractDataFrameBuilder.INTERNAL_FIELDS:
            data_0.pop(key)
        expected_data_0 = {
            u'gps': u'-1.2627557 36.7926442 0.0 30.0',
            u'_gps_latitude': u'-1.2627557',
            u'_gps_longitude': u'36.7926442',
            u'_gps_altitude': u'0.0',
            u'_gps_precision': u'30.0',
            u'kids/has_kids': u'1',
            u'info/age': u'80',
            u'kids/kids_details[1]/kids_name': u'Abel',
            u'kids/kids_details[1]/kids_age': u'50',
            u'kids/kids_details[2]/kids_name': u'Cain',
            u'kids/kids_details[2]/kids_age': u'76',
            u'web_browsers/chrome': True,
            u'web_browsers/ie': True,
            u'web_browsers/safari': False,
            u'web_browsers/firefox': False,
            u'info/name': u'Adam'
        }
        self.assertEqual(expected_data_0, data_0)

    def test_split_select_multiples(self):
        self._publish_nested_repeats_form()
        dd = self.xform.data_dictionary()
        self._submit_fixture_instance("nested_repeats", "01")
        csv_df_builder = CSVDataFrameBuilder(self.user.username,
            self.xform.id_string)
        cursor = csv_df_builder._query_mongo()
        record = cursor[0]
        select_multiples = CSVDataFrameBuilder._collect_select_multiples(dd)
        result = CSVDataFrameBuilder._split_select_multiples(record,
            select_multiples)
        expected_result = {
            u'web_browsers/ie': True,
            u'web_browsers/safari': True,
            u'web_browsers/firefox': False,
            u'web_browsers/chrome': False
        }
        # build a new dictionary only composed of the keys we want to use in 
        # the comparison
        result = dict([(key, result[key]) for key in result.keys() if key in \
            expected_result.keys()])
        self.assertEqual(expected_result, result)

    def test_split_select_multiples_within_repeats(self):
        self.maxDiff = None
        record = {
            'name': 'Tom',
            'age': 23,
            'browser_use': [
                {
                    'browser_use/year': '2010',
                    'browser_use/browsers': 'firefox safari'
                },
                {
                    'browser_use/year': '2011',
                    'browser_use/browsers': 'firefox chrome'
                }
            ]
        }
        expected_result = {
            'name': 'Tom',
            'age': 23,
            'browser_use': [
                {
                    'browser_use/year': '2010',
                    'browser_use/browsers/firefox': True,
                    'browser_use/browsers/safari': True,
                    'browser_use/browsers/ie': False,
                    'browser_use/browsers/chrome': False
                },
                {
                    'browser_use/year': '2011',
                    'browser_use/browsers/firefox': True,
                    'browser_use/browsers/safari': False,
                    'browser_use/browsers/ie': False,
                    'browser_use/browsers/chrome': True
                }
            ]
        }
        select_multiples = {
            'browser_use/browsers':
                [
                    'browser_use/browsers/firefox',
                    'browser_use/browsers/safari',
                    'browser_use/browsers/ie',
                    'browser_use/browsers/chrome'
                ]
            }
        result = CSVDataFrameBuilder._split_select_multiples(record,
            select_multiples)
        self.assertEqual(expected_result, result)

    def test_split_gps_fields(self):
        record = {
            'gps': '5 6 7 8'
        }
        gps_fields = ['gps']
        expected_result = {
            'gps': '5 6 7 8',
            '_gps_latitude': '5',
            '_gps_longitude': '6',
            '_gps_altitude': '7',
            '_gps_precision': '8',
        }
        AbstractDataFrameBuilder._split_gps_fields(record, gps_fields)
        self.assertEqual(expected_result, record)

    def test_split_gps_fields_within_repeats(self):
        record = \
        {
            'a_repeat':
            [
                {
                    'a_repeat/gps': '1 2 3 4'
                },
                {
                    'a_repeat/gps': '5 6 7 8'
                }
            ]
        }
        gps_fields = ['a_repeat/gps']
        expected_result = \
        {
            'a_repeat':
            [
                {
                    'a_repeat/gps': '1 2 3 4',
                    'a_repeat/_gps_latitude': '1',
                    'a_repeat/_gps_longitude': '2',
                    'a_repeat/_gps_altitude': '3',
                    'a_repeat/_gps_precision': '4',
                },
                {
                    'a_repeat/gps': '5 6 7 8',
                    'a_repeat/_gps_latitude': '5',
                    'a_repeat/_gps_longitude': '6',
                    'a_repeat/_gps_altitude': '7',
                    'a_repeat/_gps_precision': '8',
                }
            ]
        }
        AbstractDataFrameBuilder._split_gps_fields(record, gps_fields)
        self.assertEqual(expected_result, record)


    def test_unicode_export(self):
        unicode_char = unichr(40960)
        # fake data
        data = [{"key": unicode_char}]
        columns = ["key"]
        # test xls
        xls_df_writer = XLSDataFrameWriter(data, columns)
        temp_file = NamedTemporaryFile(suffix=".xls")
        excel_writer = ExcelWriter(temp_file.name)
        passed = False
        try:
            xls_df_writer.write_to_excel(excel_writer, "default")
            passed = True
        except UnicodeEncodeError:
            pass
        finally:
            temp_file.close()
        self.assertTrue(passed)
        # test csv
        passed = False
        csv_df_writer = CSVDataFrameWriter(data, columns)
        temp_file = NamedTemporaryFile(suffix=".csv")
        try:
            csv_df_writer.write_to_csv(temp_file)
            passed = True
        except UnicodeEncodeError:
            pass
        finally:
            temp_file.close()
        temp_file.close()
        self.assertTrue(passed)

    def test_repeat_child_name_matches_repeat(self):
        """
        ParsedInstance.to_dict creates a list within a repeat if a child has the same name as the repeat
         This test makes sure that doesnt happen
        """
        self.maxDiff = None
        fixture = "repeat_child_name_matches_repeat"
        # publish form so we have a dd to pass to xform inst. parser
        self._publish_xls_fixture_set_xform(fixture)
        submission_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "fixtures", fixture, fixture + ".xml"
        )
        # get submission xml str
        with open(submission_path, "r") as f:
            xml_str = f.read()
        dict = xform_instance_to_dict(xml_str, self.xform.data_dictionary())
        expected_dict = {
            u'test_item_name_matches_repeat': {
                u'formhub': {
                    u'uuid': u'c911d71ce1ac48478e5f8bac99addc4e'
                },
                u'gps':
                    [
                        {
                            u'info': u'Yo',
                            u'gps': u'-1.2625149 36.7924478 0.0 30.0'
                        },
                        {
                            u'info': u'What',
                            u'gps': u'-1.2625072 36.7924328 0.0 30.0'
                        }
                    ]
            }
        }
        self.assertEqual(dict, expected_dict)

    def test_remove_dups_from_list_maintain_order(self):
        l = ["a", "z", "b", "y", "c", "b", "x"]
        result = remove_dups_from_list_maintain_order(l)
        expected_result = ["a", "z", "b", "y", "c", "x"]
        self.assertEqual(result, expected_result)

    def test_valid_sheet_name(self):
        sheet_names = ["sheet_1", "sheet_2"]
        desired_sheet_name = "sheet_3"
        expected_sheet_name = "sheet_3"
        generated_sheet_name = get_valid_sheet_name(desired_sheet_name,
            sheet_names)
        self.assertEqual(generated_sheet_name, expected_sheet_name)

    def test_invalid_sheet_name(self):
        sheet_names = ["sheet_1", "sheet_2"]
        desired_sheet_name = "sheet_3_with_more_than_max_expected_length"
        expected_sheet_name = "sheet_3_with_more_than_max_exp"
        generated_sheet_name = get_valid_sheet_name(desired_sheet_name,
            sheet_names)
        self.assertEqual(generated_sheet_name, expected_sheet_name)

    def test_duplicate_sheet_name(self):
        sheet_names = ["sheet_2_with_duplicate_sheet_n",
            "sheet_2_with_duplicate_sheet_1"]
        duplicate_sheet_name = "sheet_2_with_duplicate_sheet_n"
        expected_sheet_name  = "sheet_2_with_duplicate_sheet_2"
        generated_sheet_name = get_valid_sheet_name(duplicate_sheet_name,
            sheet_names)
        self.assertEqual(generated_sheet_name, expected_sheet_name)
