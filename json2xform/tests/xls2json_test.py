"""
Testing simple cases for JSON2XForm
"""
import sys, os

sys.path.append('/Users/alexdorey/Code/NMIS/mongo/nmis')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'


from django.test import TestCase, Client

import json

from json2xform.xls2json import XlsForm

class ConvertXls2JSON(TestCase):

    def test_simple_yes_or_no_question(self):
        x = XlsForm("json2xform/surveys/super_simple/yes_or_no_question.xls")
        x_results = x.to_dict()
        
        expected_dict = [{u'choices': [{u'text': {u'english': u'yes'}, u'value': u'yes'},
                      {u'text': {u'english': u'no'}, u'value': u'no'}],
                         u'name': u'good_day', u'type': u'select one',
                         u'text': {u'english': u'have you had a good day today?'}}]
        
        self.assertEqual(x_results, expected_dict)
