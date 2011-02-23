"""
Testing simple cases for Xls2Json
"""
import sys, os

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.test import TestCase, Client
from json2xform.xls2json import ExcelReader
from json2xform.builder import create_survey_element_from_dict

class GroupTests(TestCase):

    def test_json(self):
        x = ExcelReader("json2xform/tests/group.xls")
        x_results = x.to_dict()
        expected_dict = {
            u'name': 'group',
            u'type': u'survey',
            u'children': [
                {
                    u'name': u'family_name',
                    u'type': u'text',
                    u'label': {u'English': u"What's your family name?"}
                    },
                {
                    u'name': u'father',
                    u'type': u'group',
                    u'label': {u'English': u'Father'},
                    u'children': [
                        {
                            u'name': u'phone_number',
                            u'type': u'phone number',
                            u'label': {u'English': u"What's your father's phone number?"}
                            },
                        {
                            u'name': u'age',
                            u'type': u'integer',
                            u'label': {u'English': u'How old is your father?'}
                            }
                        ],
                    }
                ],
            }
        self.assertEqual(x_results, expected_dict)

    def test_equality_of_to_dict(self):
        x = ExcelReader("json2xform/tests/group.xls")
        x_results = x.to_dict()

        survey_object = create_survey_element_from_dict(x_results)
        self.assertEqual(x_results, survey_object.to_dict())
