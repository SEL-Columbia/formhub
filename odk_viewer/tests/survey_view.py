import json
import re

from django.test import TestCase
from django.core.urlresolvers import reverse
from pyxform import create_survey_from_xls

from main.tests.test_base import MainTestCase
from odk_logger.models import XForm, Instance
from odk_viewer.models import ParsedInstance, DataDictionary
from odk_viewer.views import survey_responses
from odk_logger.xform_instance_parser import xform_instance_to_dict
from odk_viewer.xls_writer import XlsWriter
from odk_viewer.csv_writer import CsvWriter
from utils.export_tools import DictOrganizer


class TestSurveyView(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        self.survey = create_survey_from_xls("odk_viewer/tests/name_survey.xls")
        json_str = json.dumps(self.survey.to_json_dict())
        self.data_dictionary = DataDictionary.objects.create(
            xml=self.survey.to_xml(), json=json_str, user = self.user)

        info = {
            "survey_name" : self.survey.name,
            "id_string" : self.survey.id_string,
            "name" : "Andrew"
            }
        xml_str = u'<?xml version=\'1.0\' ?><%(survey_name)s id="%(id_string)s"><name>%(name)s</name></%(survey_name)s>' % info
        self.instance = Instance.objects.create(xml=xml_str, user=self.user)
        ParsedInstance.objects.get_or_create(instance=self.instance)
        self.parsed_instance = ParsedInstance.objects.get(
                instance=self.instance)

    def test_survey_view(self):
        url = reverse(survey_responses, kwargs={
                'instance_id' : self.parsed_instance.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        expected_html = '''

<table class="table table-bordered table-striped">
  <thead>
    <tr>
      <th>Question</th>
      <th>Response</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>
        <span class="language Unknown">What&#39;s your name?</span>
      </td>
      <td>Andrew</td>
    </tr>
  </tbody>
</table>
<script type="text/javascript">_StatHat.push([\'_trackCount\', \'nDdz7zH1c26BwPwOzF0_fyBMc2Fl\', 1.0]);</script>
'''
        self.assertEqual(expected_html, response.content)

    def test_xls_writer(self):
        xls_writer = XlsWriter()
        xls_writer.set_file()
        xls_writer.write_tables_to_workbook([
            ('table one', [['column header 1', 'column header 2'], [1, 2,]]),
            ('table two', [['1,1', '1,2'], ['2,1', '2,2']])
            ])
        file_object = xls_writer.save_workbook_to_file()
        # I guess we should read the excel file and make sure it has
        # the right stuff. I looked at it, but writing that test
        # doesn't seem worth it.

    def test_dict_organizer(self):
        serious_xml = u'''
        <?xml version=\'1.0\' ?>
          <household>
            <number_of_members>10</number_of_members>
            <man><name>Alex</name></man>
            <man><name>Bob</name></man>
            <woman>
              <name>Carla</name>
              <child><name>Danny</name></child>
              <child><name>Ed</name></child>
            </woman>
            <woman>
              <name>Fran</name>
              <child><name>Greg</name></child>
            </woman>
          </household>'''
        serious_xml = re.sub(r">\s+<", "><", serious_xml)
        d = xform_instance_to_dict(serious_xml)
        dict_organizer = DictOrganizer()
        expected_dict = {
            u'household': [
                {u'_parent_table_name': u'',
                 u'_parent_index': -1,
                 u'number_of_members': u'10',
                 u'_index': 0}
                ],
            u'woman': [
                {u'_parent_table_name': u'household',
                 u'_parent_index': 0,
                 u'name': u'Carla',
                 u'_index': 0},
                {u'_parent_table_name': u'household',
                 u'_parent_index': 0,
                 u'name': u'Fran',
                 u'_index': 1}
                ],
            u'man': [
                {u'_parent_table_name': u'household',
                 u'_parent_index': 0,
                 u'name': u'Alex',
                 u'_index': 0},
                {u'_parent_table_name': u'household',
                 u'_parent_index': 0,
                 u'name': u'Bob',
                 u'_index': 1}],
            u'child': [
                {u'_parent_table_name': u'woman',
                 u'_parent_index': 0,
                 u'name': u'Danny',
                 u'_index': 0},
                {u'_parent_table_name': u'woman',
                 u'_parent_index': 0,
                 u'name': u'Ed',
                 u'_index': 1},
                {u'_parent_table_name': u'woman',
                 u'_parent_index': 1,
                 u'name': u'Greg',
                 u'_index': 2}]}
        self.assertEqual(
            dict_organizer.get_observation_from_dict(d),
            expected_dict
            )

    def test_csv_writer(self):
        dd_writer = CsvWriter(self.data_dictionary)
        self.assertEqual(dd_writer._keys, self.data_dictionary.get_keys())
