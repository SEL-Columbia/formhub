"""
Test that surveys can be imported into the ImportedSurvey object
"""
import sys, os

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.test import TestCase, Client
from json2xform import *

from copy import copy

class Json2XformVerboseSurveyCreationTests(TestCase):
    
    def test_simple_survey_can_be_imported(self):
        small_step_label_hint = {
            'name': 'smallstep',
            'label': {'eng': 'Who landed on the moon?'},
            'hint': {'eng': 'Uzzbay Aldrinay'}
        }
        small_step_question_dict = copy(small_step_label_hint)
        small_step_question_dict.update({'type':'text'})
        
        survey = Survey(name="OneSmallStep")
        survey.add_child(create_survey_element_from_dict(small_step_question_dict))
        
        isurvey = ImportedSurvey(survey=survey)
        
        self.assertEqual(isurvey.label_hint_list(), [small_step_label_hint])

        