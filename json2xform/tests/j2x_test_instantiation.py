"""
Testing the instance object for json2xform.
"""
import sys, os

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.test import TestCase, Client
from json2xform import *
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
        i = SurveyInstance(surv)
        
        i.answer(name="color", value="blue")
        self.assertEquals(i.answers()[u'color'], "blue")
        
        i.answer(name="feeling", value="liquidy")
        self.assertEquals(i.answers()[u'feeling'], "liquidy")
        
    def test_answers_can_be_imported_from_xml(self):
        surv = Survey(name="data")
        
        surv.add_child(create_survey_element_from_dict({ \
                                'type':'text', 'name':'name'}))
        surv.add_child(create_survey_element_from_dict({ \
                                'type':'integer', 'name':'users_per_month'}))
        surv.add_child(create_survey_element_from_dict({ \
                                'type':'gps', 'name':'geopoint'}))
        surv.add_child(create_survey_element_from_dict({ \
                                'type':'imei', 'name':'device_id'}))
        
        instance = surv.instantiate()
        instance.import_from_xml("""
        <?xml version='1.0' ?><data id="build_WaterSimple_1295821382"><name>JK Resevoir</name><users_per_month>300</users_per_month><geopoint>40.783594633609184 -73.96436698913574 300.0 4.0</geopoint></data>
        """.strip())
        
        print instance.__unicode__()
        
    def test_simple_registration_xml(self):
        reg_xform = Survey(name="Registration")
        name_question = create_survey_element_from_dict({'type':'text','name':'name'})
        reg_xform.add_child(name_question)
        
        reg_instance = reg_xform.instantiate()
        
        reg_instance.answer(name="name", value="bob")
        
#        rdict = reg_instance.to_dict()
        expected_dict = {"node_name" : "Registration", \
                "id": reg_xform.id_string(), \
                "children": [{'node_name':'name', 'value':'bob'}]}
        
#        self.assertEqual(rdict, expected_dict)

        rx = reg_instance.to_xml()
        expected_xml = """<?xml version='1.0' ?><Registration id="%s"><name>bob</name></Registration>""" % \
                    (reg_xform.id_string())
        self.assertEqual(rx, expected_xml)
