import os
import csv
from django.core.urlresolvers import reverse
from tempfile import NamedTemporaryFile
from odk_logger.models.xform import XForm
from main.tests.test_base import MainTestCase
from odk_logger.xform_instance_parser import xform_instance_to_dict
from odk_viewer.pandas_mongo_bridge import *
from common_tags import NA_REP

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
        self._submission_time='2013-02-18 15:54:01'

    def _publish_xls_fixture_set_xform(self, fixture):
        """
        Publish an xls file at tests/fixtures/[fixture]/fixture.xls
        """
        xls_file_path = xls_filepath_from_fixture_name(fixture)
        count = XForm.objects.count()
        response = self._publish_xls_file(xls_file_path)
        self.assertEqual(XForm.objects.count(), count + 1)
        self.xform = XForm.objects.all().reverse()[0]

    def _submit_fixture_instance(
            self, fixture, instance, submission_time=None):
        """
        Submit an instance at
        tests/fixtures/[fixture]/instances/[fixture]_[instance].xml
        """
        xml_submission_file_path = xml_inst_filepath_from_fixture_name(fixture,
            instance)
        self._make_submission(
            xml_submission_file_path, forced_submission_time=submission_time)
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
        section_keys = xls_df_builder.sections.keys()
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
            u"info/name",
            u"meta/instanceID"
        ] + AbstractDataFrameBuilder.ADDITIONAL_COLUMNS +\
                                   XLSDataFrameBuilder.EXTRA_COLUMNS
        # get the header
        default_columns = [k for k in data[self.survey_name][0]]
        self.assertEqual(sorted(expected_default_columns),
            sorted(default_columns))

        # columns in the kids_details sheet
        expected_kids_details_columns = [
            u"kids/kids_details/kids_name",
            u"kids/kids_details/kids_age"
        ] + AbstractDataFrameBuilder.ADDITIONAL_COLUMNS +\
                                        XLSDataFrameBuilder.EXTRA_COLUMNS
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
            u"meta/instanceID"
        ] + AbstractDataFrameBuilder.ADDITIONAL_COLUMNS +\
                                   XLSDataFrameBuilder.EXTRA_COLUMNS
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
        url = reverse('xls_export',
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
        url = reverse('xls_export',
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
        self._submit_fixture_instance(
            "nested_repeats", "01", submission_time=self._submission_time)
        self._submit_fixture_instance(
            "nested_repeats", "02", submission_time=self._submission_time)
        csv_df_builder = CSVDataFrameBuilder(self.user.username,
            self.xform.id_string)
        temp_file = NamedTemporaryFile(suffix=".csv", delete=False)
        csv_df_builder.export_to(temp_file.name)
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
        ] + AbstractDataFrameBuilder.ADDITIONAL_COLUMNS +\
                           AbstractDataFrameBuilder.IGNORED_COLUMNS
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
        for key in AbstractDataFrameBuilder.IGNORED_COLUMNS:
            data_0.pop(key)
        for key in AbstractDataFrameBuilder.ADDITIONAL_COLUMNS:
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
            u'info/name': u'Adam',
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

    def test_query_mongo(self):
        """
        Test querying for record count and records using AbstractDataFrameBuilder._query_mongo
        """
        self._publish_single_level_repeat_form()
        # submit 3 instances
        for i in range(3):
            self._submit_fixture_instance("new_repeats", "01")
        df_builder = XLSDataFrameBuilder(self.user.username,
            self.xform.id_string)
        record_count = df_builder._query_mongo(count=True)
        self.assertEqual(record_count, 3)
        cursor = df_builder._query_mongo()
        records = [record for record in cursor]
        self.assertTrue(len(records), 3)
        # test querying using limits
        cursor = df_builder._query_mongo(start=2, limit=2)
        records = [record for record in cursor]
        self.assertTrue(len(records), 1)


    def test_prefix_from_xpath(self):
        xpath = "parent/child/grandhild"
        prefix = get_prefix_from_xpath(xpath)
        self.assertEqual(prefix, 'parent/child/')
        xpath = "parent/child"
        prefix = get_prefix_from_xpath(xpath)
        self.assertEqual(prefix, 'parent/')
        xpath = "parent"
        prefix = get_prefix_from_xpath(xpath)
        self.assertTrue(prefix is None)

    def test_csv_export_with_df_size_limit(self):
        """
        To fix pandas limitation of 30k rows on csv export, we specify a max
        number of records in a dataframe on export - lets test it
        """
        self._publish_single_level_repeat_form()
        # submit 7 instances
        for i in range(4):
            self._submit_fixture_instance("new_repeats", "01")
        self._submit_fixture_instance("new_repeats", "02")
        for i in range(2):
            self._submit_fixture_instance("new_repeats", "01")
        csv_df_builder = CSVDataFrameBuilder(self.user.username,
            self.xform.id_string)
        record_count = csv_df_builder._query_mongo(count=True)
        self.assertEqual(record_count, 7)
        temp_file = NamedTemporaryFile(suffix=".csv", delete=False)
        csv_df_builder.export_to(temp_file.name, data_frame_max_size=3)
        csv_file = open(temp_file.name)
        csv_reader = csv.reader(csv_file)
        header = csv_reader.next()
        self.assertEqual(
            len(header), 17 + len(AbstractDataFrameBuilder.ADDITIONAL_COLUMNS))
        rows = []
        for row in csv_reader:
            rows.append(row)
        self.assertEqual(len(rows), 7)
        self.assertEqual(rows[4][5], NA_REP)
        # close and delete file
        csv_file.close()
        os.unlink(temp_file.name)

    def test_csv_column_indices_in_groups_within_repeats(self):
        self._publish_xls_fixture_set_xform("groups_in_repeats")
        self._submit_fixture_instance("groups_in_repeats", "01")
        dd = self.xform.data_dictionary()
        columns = dd.get_keys()
        data_0 = self._csv_data_for_dataframe()[0]
        # remove dynamic fields
        ignore_list = [
            '_uuid', 'meta/instanceID', 'formhub/uuid', '_submission_time',
            '_id', '_bamboo_dataset_id']
        for item in ignore_list:
            data_0.pop(item)
        expected_data_0 = {
#            u'_id': 1,
#            u'_uuid': u'ba6bc9d7-b46a-4d25-955e-99ec94e7b2f6',
            u'_deleted_at': None,
            u'_xform_id_string': u'groups_in_repeats',
            u'_status': u'submitted_via_web',
#            u'_bamboo_dataset_id': u'',
#            u'_submission_time': u'2013-03-20T10:50:08',
            u'name': u'Abe',
            u'age': u'88',
            u'has_children': u'1',
#            u'meta/instanceID': u'uuid:ba6bc9d7-b46a-4d25-955e-99ec94e7b2f6',
#            u'formhub/uuid': u'1c491d705d514354acd4a9e34fe7526d',
            u'_attachments': [],
            u'children[1]/childs_info/name': u'Cain',
            u'children[2]/childs_info/name': u'Abel',
            u'children[1]/childs_info/age': u'56',
            u'children[2]/childs_info/age': u'48',
            u'children[1]/immunization/immunization_received/polio_1': True,
            u'children[1]/immunization/immunization_received/polio_2': False,
            u'children[2]/immunization/immunization_received/polio_1': True,
            u'children[2]/immunization/immunization_received/polio_2': True,
            u'web_browsers/chrome': True,
            u'web_browsers/firefox': False,
            u'web_browsers/ie': False,
            u'web_browsers/safari': False,
            u'gps': u'-1.2626156 36.7923571 0.0 30.0',
            u'_geolocation': [u'-1.2626156', u'36.7923571'],
            u'_gps_latitude': u'-1.2626156',
            u'_gps_longitude': u'36.7923571',
            u'_gps_altitude': u'0.0',
            u'_gps_precision': u'30.0',
        }
        self.maxDiff = None
        self.assertEqual(data_0, expected_data_0)

    # todo: test nested repeats as well on xls
    def test_xls_groups_within_repeats(self):
        self._publish_xls_fixture_set_xform("groups_in_repeats")
        self._submit_fixture_instance("groups_in_repeats", "01")
        dd = self.xform.data_dictionary()
        columns = dd.get_keys()
        data = self._xls_data_for_dataframe()
        # remove dynamic fields
        ignore_list = [
            '_uuid', 'meta/instanceID', 'formhub/uuid', '_submission_time',
            '_id', '_bamboo_dataset_id']
        for item in ignore_list:
            # pop unwanted keys from main section
            for d in data["groups_in_repeats"]:
                if d.has_key(item):
                    d.pop(item)
            # pop unwanted keys from children's section
            for d in data["children"]:
                if d.has_key(item):
                    d.pop(item)
        # todo: add _id to xls export
        expected_data = {
            u"groups_in_repeats":
            [
                {
#                        u'_submission_time': u'2013-03-21T02:57:37',
                    u'picture': None,
                    u'has_children': u'1',
                    u'name': u'Abe',
                    u'age': u'88',
                    u'web_browsers/chrome': True,
                    u'web_browsers/safari': False,
                    u'web_browsers/ie': False,
                    u'web_browsers/firefox': False,
                    u'gps': u'-1.2626156 36.7923571 0.0 30.0',
                    u'_gps_latitude': u'-1.2626156',
                    u'_gps_longitude': u'36.7923571',
                    u'_gps_altitude': u'0.0',
                    u'_gps_precision': u'30.0',
#                        u'meta/instanceID': u'uuid:ba6bc9d7-b46a-4d25-955e-99ec94e7b2f6',
#                        u'_uuid': u'ba6bc9d7-b46a-4d25-955e-99ec94e7b2f6',
                    u'_index': 1,
                    u'_parent_table_name': None,
                    u'_parent_index': -1
                }
            ]
            ,
            u"children":
            [
                {
                    u'children/childs_info/name': u'Cain',
                    u'children/childs_info/age': u'56',
                    u'children/immunization/immunization_received/polio_1': True,
                    u'children/immunization/immunization_received/polio_2': False,
                    u'_index': 1,
                    u'_parent_table_name': u'groups_in_repeats',
                    u'_parent_index': 1,
#                        u'_submission_time': None,
#                        u'_uuid': None,
                },
                {
                    u'children/childs_info/name': u'Able',
                    u'children/childs_info/age': u'48',
                    u'children/immunization/immunization_received/polio_1': True,
                    u'children/immunization/immunization_received/polio_2': True,
                    u'_index': 2,
                    u'_parent_table_name': u'groups_in_repeats',
                    u'_parent_index': 1,
#                        u'_submission_time': None,
#                        u'_uuid': None,
                }
            ]
        }
        self.maxDiff = None
        self.assertEqual(
            data["groups_in_repeats"][0], expected_data["groups_in_repeats"][0])
        # each of the children should have children/... keys, we can guratnee the order so we cant check the values, just make sure they are not none
        self.assertEqual(len(data["children"]), 2)
        for child in data["children"]:
            self.assertTrue(child.has_key("children/childs_info/name"))
            self.assertIsNotNone(child["children/childs_info/name"])
            self.assertTrue(child.has_key("children/childs_info/age"))
            self.assertIsNotNone(child["children/childs_info/name"])
            self.assertTrue(child.has_key("children/immunization/immunization_received/polio_1"))
            self.assertEqual(type(child["children/immunization/immunization_received/polio_1"]), bool)
            self.assertTrue(child.has_key("children/immunization/immunization_received/polio_2"))
            self.assertEqual(type(child["children/immunization/immunization_received/polio_2"]), bool)
