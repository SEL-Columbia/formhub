"""
Testing creation of Surveys using verbose methods
"""
import sys, os

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.test import TestCase, Client
from json2xform import *

import json

class Json2XformVerboseSurveyCreationTests(TestCase):
    
    def test_survey_can_be_created_in_a_verbose_manner(self):
        s = Survey()
        s.set_name("Simple Survey")
        
        q = MultipleChoiceQuestion()
        q.set_name("cow_color")
        q._dict[MultipleChoiceQuestion.TYPE] = u"select one"
        
        q._add_option(label="Green", value="green")
        s.add_child(q)

        expected_dict = {
            u'name': 'Simple Survey',
            u'children': [
                {
                    u'name': 'cow_color',
                    u'type' : 'select one',
                    u'children': [
                        {
                            u'label': 'Green',
                            u'name': 'green',
                            u'value': 'green'
                            }
                        ],
                    }
                ],
            }
        
        self.assertEqual(s.to_dict(), expected_dict)
    
    def test_survey_can_be_created_in_a_slightly_less_verbose_manner(self):
        option_dict_array = [
            {'value': 'red', 'label':'Red'},
            {'value': 'blue', 'label': 'Blue'}
            ]
        
        q = MultipleChoiceQuestion(name="Favorite_Color", choices=option_dict_array)
        q._dict[MultipleChoiceQuestion.TYPE] = u"select one"
        s = Survey(name="Roses are Red", children=[q])

        expected_dict = {
            u'name': 'Roses are Red',
            u'children': [
                {
                    u'name': 'Favorite_Color',
                    u'type' : u'select one',
                    u'children': [
                        {u'label': 'Red', u'name': 'red', u'value': 'red'},
                        {u'label': 'Blue', u'name': 'blue', u'value': 'blue'}
                        ],
                    }
                ],
            }

        self.assertEqual(s.to_dict(), expected_dict)
    
    def test_two_options_cannot_have_the_same_value(self):
        q = MultipleChoiceQuestion(name="Favorite Color")
        q._add_option(value="grey", label="Gray")
        q._add_option(value="grey", label="Grey")
        self.assertRaises(Exception, q, 'validate')
    
    def test_one_section_cannot_have_two_conflicting_slugs(self):
        q1 = InputQuestion(name="YourName")
        q2 = InputQuestion(name="YourName")
        s = Survey(name="Roses are Red", children=[q1, q2])
        self.assertRaises(Exception, s, 'validate')
