from main.tests.test_base import MainTestCase
from odk_viewer.pandas_mongo_bridge import *

class TestPandasMongoBridge(MainTestCase):
    def setUp(self):
        pass

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

    def test_remove_indexes_from_xpath(self):
        xpath = "parent[2]/child/another[2]/item"
        expected_result = "parent/child/another/item"
        result = remove_indexes_from_xpath(xpath)
        self.assertEqual(expected_result, result)

    def test_groupname_w_one_index(self):
        xpath = "parent/child/another[23]/item"
        expected_result = "parent/child/another"
        result = get_groupname_from_xpath(xpath)
        self.assertEqual(expected_result, result)

    def test_groupname_w_multiple_indexes(self):
        xpath = "parent[2]/child/another[23]/item"
        expected_result = "parent/child/another"
        result = get_groupname_from_xpath(xpath)
        self.assertEqual(expected_result, result)

    def test_groupname_w_zero_indexes(self):
        xpath = "parent/child/another/item"
        expected_result = "parent/child/another"
        result = get_groupname_from_xpath(xpath)
        self.assertEqual(expected_result, result)

    def test_non_groupname(self):
        xpath = "parent"
        expected_result = None
        result = get_groupname_from_xpath(xpath)
        self.assertEqual(expected_result, result)

    def _test_pos_and_parent_pos_from_repeat(self):
        repeat = "parent[2]/child/item"
        expected_pos, expected_parent_pos = (2, 1)
        pos, parent_pos = pos_and_parent_pos_from_repeat(repeat)
        self.assertEqual(expected_pos, pos)
        self.assertEqual(expected_parent_pos, parent_pos)