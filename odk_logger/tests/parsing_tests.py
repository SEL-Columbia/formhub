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
    def _publish_and_submit_new_repeats(self):
        self._create_user_and_login()
        # publish our form which contains some some repeats
        xls_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../fixtures/new_repeats/new_repeats.xls"
        )
        response = self._publish_xls_file_and_set_xform(xls_file_path)
        self.assertEqual(self.response.status_code, 200)

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
        self._publish_and_submit_new_repeats()
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



