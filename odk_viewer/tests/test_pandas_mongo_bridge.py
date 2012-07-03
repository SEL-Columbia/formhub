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

    def test_get_groupname_from_xpath(self):
        xpath = "parent[2]/child/another[2]/item"
        expected_result = "parent[2]/child"
        result = get_groupname_from_xpath(xpath)
        self.assertEqual(expected_result, result)