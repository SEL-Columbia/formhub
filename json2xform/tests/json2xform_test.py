"""
Testing simple cases for json2xform
"""
import sys, os

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.test import TestCase, Client
from ..json2xform import survey_from_json

# TODO:
#  * test_two_questions_with_same_id_fails
#     (get this working in json2xform)

class BasicJson2XFormTests(TestCase):

    def test_two_questions_with_same_id_fails(self):
        """
        When loading in a form with two identical IDs, the form should
        not compile. This is a really bad test right now.
        """
        self.assertRaises(Exception, survey_from_json, "json2xform/surveys/super_simple/two_identical_ids.json")
