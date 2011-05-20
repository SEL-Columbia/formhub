from django.test import TestCase
from pyxform import create_survey_from_xls
from xform_manager.models import XForm, Instance
from parsed_xforms.models import ParsedInstance, DataDictionary
from parsed_xforms.views import survey_responses
from django.core.urlresolvers import reverse
import json
import re
from xform_manager.xform_instance_parser import xform_instance_to_dict
from parsed_xforms.views.xls_export import XlsWriter, DictOrganizer, DataDictionaryWriter

class TestSurveyView(TestCase):
    
    def setUp(self):
        self.survey = create_survey_from_xls("parsed_xforms/tests/name_survey.xls")
        self.xform = XForm.objects.create(xml=self.survey.to_xml())
        json_str = json.dumps(self.survey.to_dict())
        self.data_dictionary = DataDictionary.objects.create(
            xform=self.xform, json=json_str)

        info = {
            "survey_name" : self.survey.get_name(),
            "id_string" : self.survey.id_string(),
            "name" : "Andrew"
            }
        xml_str = u'<?xml version=\'1.0\' ?><%(survey_name)s id="%(id_string)s"><name>%(name)s</name></%(survey_name)s>' % info
        self.instance = Instance.objects.create(xml=xml_str)
        self.parsed_instance = ParsedInstance.objects.get(instance=self.instance)

    def test_survey_view(self):
        url = reverse(survey_responses, kwargs={'pk' : self.parsed_instance.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response_str = str(response)
        header = """Vary: Cookie
Content-Type: text/html; charset=utf-8

"""
        self.assertTrue(response_str.startswith(header))
        json_response = response_str[len(header):]
        j = json.loads(json_response)
        
        self.assertEqual(j, [[u"What's your name?", u'Andrew']])

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

    def test_data_dictionary_writer(self):        
        dd_writer = DataDictionaryWriter()
        dd_writer.set_data_dictionary(self.data_dictionary)
        self.assertEqual(dd_writer._sheets.keys(), [self.survey.get_name()])
        self.assertEqual(dd_writer._columns.keys(), [self.survey.get_name()])
        self.assertEqual(dd_writer._columns[self.survey.get_name()], [u'name'])
                         
