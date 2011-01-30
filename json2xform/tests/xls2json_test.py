"""
Testing simple cases for Xls2Json
"""
import sys, os

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.test import TestCase, Client
from json2xform.xls2json import XlsForm

class BasicXls2JsonApiTests(TestCase):

    def test_simple_yes_or_no_question(self):
        x = XlsForm("json2xform/surveys/super_simple/yes_or_no_question.xls")
        x_results = x.to_dict()
        
        expected_dict = [{u'choices': [{u'text': {u'english': u'yes'}, u'value': u'yes'},
                      {u'text': {u'english': u'no'}, u'value': u'no'}],
                         u'name': u'good_day', u'type': u'select one',
                         u'text': {u'english': u'have you had a good day today?'}}]
        
        self.assertEqual(x_results, expected_dict)


    def test_gps(self):
        x = XlsForm("json2xform/surveys/super_simple/gps.xls")

        expected_dict = [{u'type': u'gps', u'name': u'location'}]

        self.assertEqual(x.to_dict(), expected_dict)

    
    def test_string_and_integer(self):
        x = XlsForm("json2xform/surveys/super_simple/string_and_integer.xls")

        expected_dict = [{'text': {u'english': u'What is your name?'}, \
                            u'type': u'string', u'name': u'your_name'}, \
                        {'text': {u'english': u'How many years old are you?'}, \
                            u'type': u'integer', u'name': u'your_age'}]

        self.assertEqual(x.to_dict(), expected_dict)

    def test_two_questions_with_same_id_fails(self):
        """
        When loading in a form with two identical IDs, the form should not compile.
        """
        self.assertRaises(XlsForm("json2xform/surveys/super_simple/two_identical_ids.xls"), Exception)
