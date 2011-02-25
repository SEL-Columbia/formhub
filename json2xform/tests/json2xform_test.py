"""
Testing simple cases for json2xform
"""
import sys, os

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.test import TestCase, Client
#from ..json2xform import survey_from_json
from ..survey import Survey

from json2xform.builder import create_survey_element_from_dict


# TODO:
#  * test_two_questions_with_same_id_fails
#     (get this working in json2xform)

class BasicJson2XFormTests(TestCase):

    def test_survey_can_have_to_xml_called_twice(self):
        """
        Test: Survey can have "to_xml" called multiple times
        
        (This was not being allowed before.)
        
        It would be good to know (with confidence) that a survey object
        can be exported to_xml twice, and the same thing will be returned
        both times.
        """
        survey = Survey(name="SampleSurvey")
        q = create_survey_element_from_dict({'type':'text', 'name':'name'})
        survey.add_child(q)
        
        str1 = survey.to_xml()
        str2 = survey.to_xml()
        
        self.assertEqual(str1, str2)