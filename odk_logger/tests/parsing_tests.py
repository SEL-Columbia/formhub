# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.test import TestCase
from odk_logger.xform_instance_parser import xform_instance_to_dict, \
    xform_instance_to_flat_dict, parse_xform_instance, XFormInstanceParser
from odk_logger.xform_instance_parser import XFORM_ID_STRING

XML = u"xml"
DICT = u"dict"
FLAT_DICT = u"flat_dict"
ID = XFORM_ID_STRING

class TestXFormInstanceParser(TestCase):

    def setUp(self):
        self.inputs_and_outputs = [
            {
                XML: u"""<?xml version='1.0' ?><test id="test_id"><a>1</a><b>2</b></test>""",
                DICT: {
                    u"test": {
                        u"a": u"1",
                        u"b": u"2",
                        }
                    },
                FLAT_DICT: {
                    u"a": u"1",
                    u"b": u"2",
                    },
                ID : u"test_id",
                },
            {
                XML: u"""<?xml version='1.0' ?><test id="test_id"><a><b>2</b></a></test>""",
                DICT: {
                    u"test": {
                        u"a" : {
                            u"b" : u"2"
                            }
                        }
                    },
                FLAT_DICT: {
                    u"a/b" : u"2"
                    },
                ID: u"test_id"
                },
            {
                XML: u"""<?xml version='1.0' ?><test id="test_id"><b>1</b><b>2</b></test>""",
                DICT: {
                    u"test" : {
                        u"b" : [u"1", u"2"]
                        }
                    },
                FLAT_DICT: {
                    #u"b":[u"1", u"2"]
                    u"b":[{u"b": u"1"}, {u"b": u"2"}]
                },
                ID: u"test_id"
                },
            {
                XML: u"""
<?xml version='1.0' ?>
<test id="test_id">
  <a>
    <b>1</b>
  </a>
  <a>
    <b>2</b>
  </a>
</test>
""",
                DICT: {
                    u"test" : {
                        u"a" : [{u"b" : u"1"}, {u"b": u"2"}]
                        }
                    },
                FLAT_DICT: {
                    #u"a/b": u"1",
                    #u"a[2]/b": u"2"
                    u'a': [{u'a/b': u'1'}, {u'a/b': u'2'}]
                    },
                ID: u"test_id"
                },

            ]            

    def test_parse_xform_instance(self):
        # todo: need to test id string as well
        for d in self.inputs_and_outputs:
            self.assertEqual(xform_instance_to_dict(d[XML]), d[DICT])
            self.assertEqual(xform_instance_to_flat_dict(d[XML]), d[FLAT_DICT])
            flat_dict_with_id = {ID: d[ID]}
            flat_dict_with_id.update(d[FLAT_DICT])
            self.assertEqual(parse_xform_instance(d[XML]), flat_dict_with_id)

    def test_parse_xform_nested_repeats(self):
        xml = """<?xml version='1.0' ?><new_repeats id="new_repeat"><info><name>Adam</name><age>80</age></info><kids><has_kids>1</has_kids><kids_details><kids_name>Abel</kids_name><kids_age>50</kids_age></kids_details><kids_details><kids_name>Cain</kids_name><kids_age>74</kids_age></kids_details></kids><gps>-1.2627557 36.7926442 0.0 30.0</gps><web_browsers>chrome ie</web_browsers></new_repeats>"""
        parser = XFormInstanceParser(xml)
        dict = parser.to_dict()
        expected_dict = {
            u'new_repeats':
                {
                    u'info':
                    {
                        u'age': u'80',
                        u'name': u'Adam'
                    },
                    u'kids':
                    {
                        u'kids_details':
                        [
                            {
                                u'kids_age': u'50',
                                u'kids_name': u'Abel'
                            },
                            {
                                u'kids_age': u'74',
                                u'kids_name': u'Cain'
                            }
                        ],
                        u'has_kids': u'1'
                    },
                    u'web_browsers': u'chrome ie',
                    u'gps': u'-1.2627557 36.7926442 0.0 30.0'
                }
        }
        flat_dict = parser.to_flat_dict()
        expected_flat_dict = {
            u'gps': u'-1.2627557 36.7926442 0.0 30.0',
            u'kids/kids_details':
            [
                {
                    u'kids/kids_details/kids_name': u'Abel',
                    u'kids/kids_details/kids_age': u'50'
                },
                {
                    u'kids/kids_details/kids_name': u'Cain',
                    u'kids/kids_details/kids_age': u'74'
                }
            ],
            u'kids/has_kids': u'1',
            u'info/age': u'80',
            u'web_browsers': u'chrome ie',
            u'info/name': u'Adam'
        }
        expected_flat_dict2 = {
            u'info/age': u'80',
            u'gps': u'-1.2627557 36.7926442 0.0 30.0',
            u'kids/kids_details/kids_name': u'Abel',
            u'kids/kids_details[2]/kids_name': u'Cain',
            u'kids/has_kids': u'1',
            u'kids/kids_details[2]/kids_age': u'74',
            u'kids/kids_details/kids_age': u'50',
            u'web_browsers': u'chrome ie', u'info/name': u'Adam'
        }
        self.assertEqual(flat_dict, expected_flat_dict)

