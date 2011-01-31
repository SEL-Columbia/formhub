"""
Testing simple cases for json2xform
"""
import sys, os

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.test import TestCase, Client
from json2xform.xls2json import XlsForm

# TODO:
#  * test_two_questions_with_same_id_fails
#     (get this working in json2xform)

class BasicJson2XFormTests(TestCase):

    def test_two_questions_with_same_id_fails(self):
        # we need to rewrite this test when we actually add this
        # feature to json2xform
        # self.assertRaises(XlsForm("json2xform/surveys/super_simple/two_identical_ids.json"), Exception)
        """
        When loading in a form with two identical IDs, the form should not compile.
        """
        pass
