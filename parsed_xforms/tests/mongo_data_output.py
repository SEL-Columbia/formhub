"""
Testing that data in parsed instance's mongo_dict is properly categorized.
"""
from django.test import TestCase, Client
from xform_manager.models import Instance, XForm
from surveyor_manager.models import Surveyor
from datetime import datetime

class TestMongoData(TestCase):

    def test_simple_xpath_dict(self):
        from parsed_xforms.models import categorize_from_xpath_structure
        
        sample_xpath_dict = {
            'onekey': 'value',
            'category/key': 'value',
            'category/key2': 'value',
            'category2/key': 'value',
            'category2/key2': 'value',
            'supercategory/category/key': 'value',
            'supercategory/category/key2': 'value'
        }
        
        expected_dict = {
            'onekey': 'value',
            'category': {
                'key': 'value',
                'key2': 'value'
            },
            'category2': {
                'key': 'value',
                'key2': 'value'
            },
            'supercategory': {
                'category': {
                    'key': 'value',
                    'key2': 'value'
                }
            }
        }
        
        result = categorize_from_xpath_structure(sample_xpath_dict)
        self.assertEqual(result, expected_dict)
