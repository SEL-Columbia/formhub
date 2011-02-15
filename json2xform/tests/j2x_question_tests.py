"""
Testing creation of Surveys using verbose methods
"""
import sys, os

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.test import TestCase, Client
from .json2xform import *

import json

loaded_question_types = [{u'bind': {u'type': u'string'}, u'name': u'load imei'}, \
                          {u'bind': {u'type': u'decimal'}, u'control_xml_tag': u'input', u'name': u'decimal'}, \
                          {u'bind': {u'type': u'geopoint'}, u'control_xml_tag': u'input', u'name': u'gps'}]



class Json2XformQuestionValidationTests(TestCase):
    
    def test_multiple_choice_must_have_multiple_choices(self):
        pass
        
    def test_question_type_is_loaded(self):
        i = InputQuestion(name="Gimme a decimal?", question_type="decimal")
        self.assertEqual(i._question_type, "decimal")
