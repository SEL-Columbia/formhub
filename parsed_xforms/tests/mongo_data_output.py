"""
Testing that data in parsed instance's mongo_dict is properly categorized.
"""
from django.test import TestCase, Client
from parsed_xforms.models import categorize_from_xpath_structure
from datetime import datetime

class TestMongoData(TestCase):

    def test_simple_xpath_dict(self):
        sample_xpath_dict = {
            'onekey': 'val1',
            'category/key': 'val1',
            'category/key2': 'val2',
            'category2/key': 'val1',
            'category2/key2': 'val2',
            'supercategory/category/key': 'val1',
            'supercategory/category/key2': 'val2'
        }
        
        expected_dict = {
            'onekey': 'val1',
            'category': {
                'key': 'val1',
                'key2': 'val2'
            },
            'category2': {
                'key': 'val1',
                'key2': 'val2'
            },
            'supercategory': {
                'category': {
                    'key': 'val1',
                    'key2': 'val2'
                }
            }
        }
        
        result = categorize_from_xpath_structure(sample_xpath_dict)
        self.assertEqual(result, expected_dict)
