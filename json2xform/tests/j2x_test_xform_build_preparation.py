"""
Testing preparation of values for XForm exporting
"""
import sys, os

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.test import TestCase, Client
from json2xform import *

import json

class Json2XformExportingPrepTests(TestCase):
    
    def test_dictionary_consolidates_duplicate_entries(self):
        
        yes_or_no_dict_array = [{ "text": {"French":"Oui", "English": "Yes"}, "value": "yes"}, \
                {"text": {"French": "Non", "English": "No"}, "value": "no"}]
        
        first_yesno_question = MultipleChoiceQuestion(name="yn_q1", options=yes_or_no_dict_array)
        second_yesno_question = MultipleChoiceQuestion(name="yn_q2", options=yes_or_no_dict_array)
        
        s = Survey(name="Yes Or No Tests")
        s.add_child(first_yesno_question)
        s.add_child(second_yesno_question)
        
        #begin the processes in survey.to_xml()
        # 1. validate()
        s.validate()
        
        # 2. survey._build_options_list_from_descendants()
        options_list = s._build_options_list_from_descendants()
        # Is this method called somewhere else now?
        
        desired_options_list = [first_yesno_question._options]
        
        self.assertEqual(options_list, desired_options_list)
        
        self.assertEqual(first_yesno_question._option_list_index_number, 0)
        self.assertEqual(second_yesno_question._option_list_index_number, 0)


