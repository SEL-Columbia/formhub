import json
import os
import re
from django.core.urlresolvers import reverse
from main.tests.test_base import MainTestCase
from odk_logger.models.instance import Instance
from odk_logger.views import edit_data
from odk_viewer.models.parsed_instance import ParsedInstance
from utils.logger_tools import inject_instanceid
from odk_logger.xform_instance_parser import get_uuid_from_xml


class TestWebforms(MainTestCase):
    def setUp(self):
        super(TestWebforms, self).setUp()
        self._publish_transportation_form_and_submit_instance()

    def test_edit_url(self):
        instance = Instance.objects.order_by('id').reverse()[0]
        edit_url = reverse(edit_data, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string,
            'data_id': instance.id
        })
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 302)

    def test_inject_instanceid(self):
        """
        Test that 1 and only 1 instance id exists or is injected
        """
        instance = Instance.objects.all().reverse()[0]
        with open(
            os.path.join(
                os.path.dirname(__file__), "..", "fixtures", "tutorial",
                "instances", "tutorial_2012-06-27_11-27-53.xml"),
            "r") as xml_file:
            xml_str = xml_file.read()
        # test that we dont have an instance id
        uuid = get_uuid_from_xml(xml_str)
        self.assertIsNone(uuid)
        injected_xml_str = inject_instanceid(xml_str, instance.uuid)
        # check that xml has the instanceid tag
        uuid = get_uuid_from_xml(injected_xml_str)
        self.assertEqual(uuid, instance.uuid)

    def test_dont_inject_instanceid_if_exists(self):
        xls_file_path = os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "fixtures",
                    "tutorial",
                    "tutorial.xls"
                )
        self._publish_xls_file_and_set_xform(xls_file_path)
        xml_file_path = os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "fixtures",
                    "tutorial",
                    "instances",
                    "tutorial_2012-06-27_11-27-53_w_uuid.xml"
                )
        self._make_submission(xml_file_path)
        instance = Instance.objects.order_by('id').reverse()[0]
        injected_xml_str = inject_instanceid(instance.xml, instance.uuid)
        # check that the xml is unmodified
        self.assertEqual(instance.xml, injected_xml_str)
