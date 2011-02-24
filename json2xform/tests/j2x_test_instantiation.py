"""
Testing the instance object for json2xform.
"""
import sys, os

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.test import TestCase, Client
from json2xform import *
from json2xform.instance import SurveyInstance as Instance
from json2xform.builder import create_survey_element_from_dict

class Json2XformExportingPrepTests(TestCase):
    
    def test_simple_survey_instantiation(self):
        surv = Survey(name="Simple")
        q = create_survey_element_from_dict({"type":"text", "name":"survey_question"})
        surv.add_child(q)
        
        i = surv.instantiate()
        
        self.assertEquals(i.keys(), ["survey_question"])
        self.assertEquals(set(i.xpaths()), set([\
            u"/Simple", \
            u"/Simple/survey_question", \
        ]))
    
    def test_simple_survey_answering(self):
        surv = Survey(name="Water")
        q = create_survey_element_from_dict({"type":"text", "name":"color"})
        q2 = create_survey_element_from_dict({"type":"text", "name":"feeling"})
        
        surv.add_child(q)
        surv.add_child(q2)
        i = Instance(surv)
        
        i.answer(xpath="/Water/color", value="blue")
        self.assertEquals(i.answers()[u'/Water/color'], "blue")
        
        i.answer(name="feeling", value="liquidy")
        self.assertEquals(i.answers()[u'/Water/feeling'], "liquidy")
        
    def test_answers_can_be_imported_from_xml(self):
        surv = Survey(name="data")
        
        surv.add_child(create_survey_element_from_dict({ \
                                'type':'text', 'name':'name'}))
        surv.add_child(create_survey_element_from_dict({ \
                                'type':'integer', 'name':'users_per_month'}))
        surv.add_child(create_survey_element_from_dict({ \
                                'type':'gps', 'name':'geopoint'}))
        surv.add_child(create_survey_element_from_dict({ \
                                'type':'load imei', 'name':'device_id'}))
        
        instance = surv.instantiate()
        instance.import_from_xml("""
        <?xml version='1.0' ?><data id="build_WaterSimple_1295821382"><name>JK Resevoir</name><users_per_month>300</users_per_month><geopoint>40.783594633609184 -73.96436698913574 300.0 4.0</geopoint></data>
        """.strip())
        
        print instance.__unicode__()
