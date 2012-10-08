import json
import os
import re
from django.core.urlresolvers import reverse
from main.tests.test_base import MainTestCase
from odk_logger.models.instance import Instance
from odk_logger.views import edit_data
from odk_viewer.models.parsed_instance import ParsedInstance
from utils.logger_tools import inject_instanceid

class TestWebforms(MainTestCase):
    def setUp(self):
        super(TestWebforms, self).setUp()
        self._publish_transportation_form_and_submit_instance()

    def test_edit_url(self):
        instance = Instance.objects.all().reverse()[0]
        query = json.dumps({'_uuid': instance.uuid})
        cursor = ParsedInstance.query_mongo(self.user.username,
            self.xform.id_string, query, '[]', '{}')
        records = [record for record in cursor]
        self.assertTrue(len(records) > 0)
        edit_url = reverse(edit_data, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string,
            'data_id': records[0]['_id']
        })
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 302)

    def test_inject_instanceid(self):
        instance = Instance.objects.all().reverse()[0]
        injected_xml_str = inject_instanceid(instance)
        # check that xml has the instanceid tag
        regex = re.compile(r"^.+?uuid:(.+?)<")
        matches = regex.match(injected_xml_str)
        self.assertTrue(matches != None)
        self.assertTrue(len(matches.groups()), 1)
        self.assertEqual(matches.groups()[0], instance.uuid)

    def test_inject_instanceid_fail_if_exists(self):
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
        injected_xml_str = inject_instanceid(instance)
        self.assertEqual(instance.xml, injected_xml_str)
        # check that the xml is unmodified
