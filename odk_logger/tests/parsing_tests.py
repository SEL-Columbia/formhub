# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from xml.dom import minidom
import os
import re
from main.tests.test_base import MainTestCase
from odk_logger.models.xform import XForm
from odk_logger.xform_instance_parser import xform_instance_to_dict, \
    xform_instance_to_flat_dict, parse_xform_instance, XFormInstanceParser,\
    xpath_from_xml_node
from odk_logger.xform_instance_parser import XFORM_ID_STRING

XML = u"xml"
DICT = u"dict"
FLAT_DICT = u"flat_dict"
ID = XFORM_ID_STRING

class TestXFormInstanceParser(MainTestCase):

    def _setUp(self):
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

    def _test_parse_xform_instance(self):
        # todo: need to test id string as well
        for d in self.inputs_and_outputs:
            self.assertEqual(xform_instance_to_dict(d[XML]), d[DICT])
            self.assertEqual(xform_instance_to_flat_dict(d[XML]), d[FLAT_DICT])
            flat_dict_with_id = {ID: d[ID]}
            flat_dict_with_id.update(d[FLAT_DICT])
            self.assertEqual(parse_xform_instance(d[XML]), flat_dict_with_id)

    def _test_parsed_xml(self):
        self._create_user_and_login()
        # publish our form which contains some some repeats
        xls_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../fixtures/new_repeats/new_repeats.xls"
        )
        response = self._publish_xls_file(xls_file_path)
        self.assertEqual(response.status_code, 200)
        self.xform = XForm.objects.get(user=self.user, id_string="new_repeat")

        # submit an instance
        xml_submission_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../fixtures/new_repeats/instances/new_repeats_2012-07-05-14-33-53.xml"
        )
        self._make_submission(xml_submission_file_path)
        self.assertEqual(self.response.status_code, 201)

        # load xml file to parse and compare
        xml_file = open(xml_submission_file_path)
        self.xml = xml_file.read()
        xml_file.close()

    def test_parse_xform_nested_repeats(self):
        parser = XFormInstanceParser(self.xml, self.xform.data_dictionary())
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
                        ],
                        u'has_kids': u'1'
                    },
                    u'web_browsers': u'chrome ie',
                    u'gps': u'-1.2627557 36.7926442 0.0 30.0'
                }
        }
        self.assertEqual(dict, expected_dict)

        flat_dict = parser.to_flat_dict()
        expected_flat_dict = {
            u'gps': u'-1.2627557 36.7926442 0.0 30.0',
            u'kids/kids_details':
            [
                {
                    u'kids/kids_details/kids_name': u'Abel',
                    u'kids/kids_details/kids_age': u'50'
                }
            ],
            u'kids/has_kids': u'1',
            u'info/age': u'80',
            u'web_browsers': u'chrome ie',
            u'info/name': u'Adam'
        }
        self.assertEqual(flat_dict, expected_flat_dict)

    def test_xpath_from_xml_node(self):
        xml_str = '<?xml version=\'1.0\' ?><test_item_name_matches_repeat id="repeat_child_name_matches_repeat"><formhub><uuid>c911d71ce1ac48478e5f8bac99addc4e</uuid></formhub><gps><gps>-1.2625149 36.7924478 0.0 30.0</gps><info>Yo</info></gps><gps><gps>-1.2625072 36.7924328 0.0 30.0</gps><info>What</info></gps></test_item_name_matches_repeat>'
        clean_xml_str = xml_str.strip()
        clean_xml_str = re.sub(ur">\s+<", u"><", clean_xml_str)
        root_node = minidom.parseString(clean_xml_str).documentElement
        # get the first top-level gps element
        gps_node = root_node.firstChild.nextSibling
        self.assertEqual(gps_node.nodeName, u'gps')
        # get the info element within the gps element
        info_node = gps_node.getElementsByTagName(u'info')[0]
        # create an xpath that should look like gps/info
        xpath = xpath_from_xml_node(info_node)
        self.assertEqual(xpath, u'gps/info')



