from django.test import TestCase, Client
from json2xform.builder import create_survey_element_from_dict
from json2xform.xls2json import ExcelReader

class BuilderTests(TestCase):
    
    def test_create_table_from_dict(self):
        d = {
            u"type" : u"table",
            u"name" : u"my_table",
            u"label" : {u"English" : u"My Table"},
            u"columns" : [
                {
                    u"name" : u"col1",
                    u"label" : {u"English" : u"column 1"},
                    },
                {
                    u"name" : u"col2",
                    u"label" : {u"English" : u"column 2"},
                    },
                ],
            u"children" : [
                {
                    u"type": u"integer",
                    u"name": u"count",
                    u"label": {u"English": u"How many are there in this group?"}
                    },
                ]
            }
        g = create_survey_element_from_dict(d)

        expected_dict = {
            u'name': u'my_table',
            u'label': {u'English': u'My Table'},
            u'children': [
                {
                    u'name': u'col1',
                    u'label': {u'English': u'column 1'},
                    u'children': [
                        {
                            u'name': u'count',
                            u'label': {u'English': u'How many are there in this group?'},
                            u'type': u'integer'
                            }
                        ]
                    },
                {
                    u'name': u'col2',
                    u'label': {u'English': u'column 2'},
                    u'children': [
                        {
                            u'name': u'count',
                            u'label': {u'English': u'How many are there in this group?'},
                            u'type': u'integer'
                            }
                        ]
                    }
                ]
            }

        self.assertEqual(g.to_dict(), expected_dict)

    def test_specify_other(self):
        excel_reader = ExcelReader("json2xform/tests/specify_other.xls")
        d = excel_reader.to_dict()
        survey = create_survey_element_from_dict(d)
        expected_dict = {
            u'name': 'specify_other',
            u'type': u'survey',
            u'children': [
                {
                    u'name': u'sex',
                    u'label': {u'English': u'What sex are you?'},
                    u'type': u'select one',
                    u'children': [
                        {
                            u'name': u'male',
                            u'value': u'male',
                            u'label': {u'English': u'Male'}
                            },
                        {
                            u'name': u'female',
                            u'value': u'female',
                            u'label': {u'English': u'Female'}
                            },
                        {
                            u'name': u'other',
                            u'value': u'other',
                            u'label': {u'English': u'Other'}
                            }
                        ]
                    },
                {
                    u'name': u'sex_other',
                    u'bind': {u'relevant': u"selected(${sex}, 'other')"},
                    u'label': {u'English': u'What sex are you?'},
                    u'type': u'text'}
                ]
            }
        self.assertEqual(survey.to_dict(), expected_dict)
