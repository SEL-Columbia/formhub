from django.test import TestCase, Client
from json2xform.builder import create_survey_element_from_dict

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
