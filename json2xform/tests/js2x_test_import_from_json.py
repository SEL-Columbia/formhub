"""
Testing our ability to import from a JSON text file.
"""
import sys, os

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.test import TestCase, Client
from json2xform.builder import create_survey_element_from_dict

import json

class Json2XformTestJsonImport(TestCase):
    def test_simple_questions_can_be_imported_from_json(self):
        json_text = {
            "type" : "survey",
            "name" : "Exchange rate",
            "children" : [
                {
                    "label": {"French": "Combien?","English": "How many?" },
                    "type": "decimal",
                    "name": "exchange_rate"
                    }
                ]
            }
        s = create_survey_element_from_dict(json_text)
        
        self.assertEqual(s._children[0].get_type(), "decimal")
		
