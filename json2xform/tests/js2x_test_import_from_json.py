"""
Testing our ability to import from a JSON text file.
"""
import sys, os

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.test import TestCase, Client
from json2xform import *

import json

class Json2XformTestJsonImport(TestCase):
    def test_simple_questions_can_be_imported_from_json(self):
        json_text = '[{"text": {"French": "Combien?","English": "How many?" },"type": "decimal","name": "exchange_rate"}]'
        s = Survey(name="Exchange rate")
        s.load_elements_from_json(json_text)
        
        self.assertEqual(s._children[0].get_type(), "decimal")
		
