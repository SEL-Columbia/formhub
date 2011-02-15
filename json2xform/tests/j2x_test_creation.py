"""
Testing creation of Surveys using verbose methods
"""
import sys, os

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.test import TestCase, Client
from .json2xform import *

import json

class Json2XformVerboseSurveyCreationTests(TestCase):
    
    def test_survey_can_be_created_in_a_verbose_manner(self):
        s = Survey()
        s._name = "Simple Survey"
        
        q = MultipleChoiceQuestion()
        q._name = "cow_color"
        
        q._add_option(text="Green", value="green")
        s._add_element(q)
        
        self.assertEqual(s.to_dict(), { 'name': 'Simple Survey', \
            'elements': [{'name': 'cow_color', 'options': \
            [{'value': 'green', 'text': 'Green'}]}]})
    
    def test_survey_can_be_created_in_a_slightly_less_verbose_manner(self):
        option_dict_array = [\
            {'value': 'red', 'text':'Red'}, \
            {'value': 'blue', 'text': 'Blue'}]
        
        q = MultipleChoiceQuestion(name="Favorite Color", options=option_dict_array)
        s = Survey(name="Roses are Red", elements=[q])
        self.assertEqual(s.to_dict(), {'name': 'Roses are Red', \
            'elements': [{'name': 'Favorite Color', \
            'options': [{'text': 'Red','value': 'red'},{'text': 'Blue','value': 'blue'}] \
            }] \
        })
    
    def test_two_options_cannot_have_the_same_value(self):
        q = MultipleChoiceQuestion(name="Favorite Color")
        q._add_option(value="grey", text="Gray")
        q._add_option(value="grey", text="Grey")
        self.assertRaises(Exception, q, 'validate')
    
    def test_one_section_cannot_have_two_conflicting_slugs(self):
        q1 = InputQuestion(name="YourName")
        q2 = InputQuestion(name="YourName")
        s = Survey(name="Roses are Red", elements=[q1, q2])
        self.assertRaises(Exception, s, 'validate')
