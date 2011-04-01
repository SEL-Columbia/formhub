from django.test import TestCase
from pyxform import create_survey_from_xls
from xform_manager.models import XForm, Instance
from parsed_xforms.models import ParsedInstance
from parsed_xforms.views import survey_responses
from data_dictionary.models import DataDictionary
from django.core.urlresolvers import reverse
import json
import re

class TestSurveyView(TestCase):
    
    def setUp(self):
        survey = create_survey_from_xls("parsed_xforms/tests/name_survey.xls")
        self.xform = XForm.objects.create(xml=survey.to_xml())
        json_str = json.dumps(survey.to_dict())
        self.data_dictionary = DataDictionary.objects.create(
            xform=self.xform, json=json_str)

        info = {
            "survey_name" : survey.get_name(),
            "id_string" : survey.id_string(),
            "name" : "Andrew"
            }
        xml_str = u'<?xml version=\'1.0\' ?><%(survey_name)s id="%(id_string)s"><name>%(name)s</name></%(survey_name)s>' % info
        self.instance = Instance.objects.create(xml=xml_str)
        self.parsed_instance = ParsedInstance.objects.get(instance=self.instance)

    def test_survey_view(self):
        url = reverse(survey_responses, kwargs={'pk' : self.parsed_instance.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        json_response = re.sub("Content-Type: text/html; charset=utf-8", "", str(response)).strip()
        j = json.loads(json_response)
        
        self.assertEqual(j, [[u"What's your name?", u'Andrew']])
