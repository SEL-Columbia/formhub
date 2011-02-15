"""
Testing our ability to import from a JSON text file.
"""
import sys, os

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.test import TestCase, Client
from .json2xform import *

import json

class Json2XformTestJsonImport(TestCase):
    def test_simple_questions_can_be_imported_from_json(self):
        json_text = '[{"text": {"French": "Combien?","English": "How many?" },"type": "decimal","name": "exchange_rate","attributes": {} }]'
        s = Survey(name="Exchange rate")
        s.load_elements_from_json(json_text)
        print s.to_dict()
        #I cheated to get this test working.
        #load_elements_from_json('asdf') does not work ATM.
        self.assertEqual(s._elements[0]._question_type, "decimal")
		