from main.tests.test_base import MainTestCase
from odk_viewer.pandas_mongo_bridge import *

class TestPandasMongoBridge(MainTestCase):
    def setUp(self):
        pass

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