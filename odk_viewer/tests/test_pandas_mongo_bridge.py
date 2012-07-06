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