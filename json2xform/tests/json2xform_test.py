"""
Testing simple cases for json2xform
"""
import sys, os

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.test import TestCase, Client
#from ..json2xform import survey_from_json
from ..survey import Survey

# TODO:
#  * test_two_questions_with_same_id_fails
#     (get this working in json2xform)

class BasicJson2XFormTests(TestCase):

    def test_two_questions_with_same_id_fails(self):
        pass