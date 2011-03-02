"""
Testing creation of Surveys using verbose methods
"""
import sys, os

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.test import TestCase, Client
from json2xform import *
from json2xform.question import Question
from json2xform.builder import create_survey_element_from_dict

import json

from ..utils import E, ns, etree

TESTING_BINDINGS = True

def ctw(control):
    """
    ctw stands for control_test_wrap, but ctw is shorter and easier. using begin_str and end_str to
    take out the wrap that lxml gives us
    """
    begin_str = '<test xmlns:h="http://www.w3.org/1999/xhtml" xmlns:ev="http://www.w3.org/2001/xml-events" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:jr="http://openrosa.org/javarosa" xmlns="http://www.w3.org/2002/xforms">'
    end_str = '</test>'
    xml_str = etree.tostring(E("{}test", control), pretty_print=False).replace(begin_str, "").replace(end_str, "")
    return xml_str

class Json2XformQuestionValidationTests(TestCase):
    
    def setUp(self):
        self.s = Survey(name="test")
    
    def test_question_type_string(self):
        simple_string_json = {
            "label": {
                "French": "Nom du travailleur agricole:",
                "English": "Name of Community Agricultural Worker"
                },
            "type": "text",
            "name": "enumerator_name"
            }

        q = create_survey_element_from_dict(simple_string_json)
        
        expected_string_control_xml = """<input ref="/test/enumerator_name"><label ref="jr:itext('/test/enumerator_name:label')"/><hint ref="jr:itext('/test/enumerator_name:hint')"/></input>"""
        
        expected_string_binding_xml = """
        <bind nodeset="/test/enumerator_name" type="string" required="true()"/>
        """.strip()
        
        self.s.add_child(q)
        self.assertEqual(ctw(q.xml_control()), expected_string_control_xml)
        
        if TESTING_BINDINGS:
            self.assertEqual(ctw(q.xml_binding()), expected_string_binding_xml)
    
    def test_select_one_question_multilingual(self):
        """
        Test the lowest common denominator of question types.
        """
        simple_select_one_json = {
            "label" : {"f": "ftext","e": "etext"},
            "type" : "select one",
            "name" : "qname",
            "choices" : [
                {"label": {"f": "fa","e": "ea"},"value": "a"},
                {"label": {"f": "fb","e": "eb"},"value": "b"}
                ]
            }
        
        # I copied the response in, since this is not our method of testing
        # valid return values.
        expected_select_one_control_xml = """<select1 ref="/test/qname"><label ref="jr:itext('/test/qname:label')"/><item><label ref="jr:itext('/test/qname/a:label')"/><value>a</value></item><item><label ref="jr:itext('/test/qname/b:label')"/><value>b</value></item></select1>"""
        
        expected_select_one_binding_xml = """
        <bind nodeset="/test/qname" type="select1" required="true()"/>
        """.strip()
        
        q = create_survey_element_from_dict(simple_select_one_json)
        self.s.add_child(q)
        self.assertEqual(ctw(q.xml_control()), expected_select_one_control_xml)
        
        if TESTING_BINDINGS:
            self.assertEqual(ctw(q.xml_binding()), expected_select_one_binding_xml)

    def test_simple_integer_question_type_multilingual(self):
        """
        not sure how integer questions should show up.
        """
        simple_integer_question = {"text": {"f": "fc", "e": "ec"}, "type": "integer", "name": "integer_q", "attributes": {}}

        expected_integer_control_xml = """
        <input ref="/test/integer_q"><label ref="jr:itext('/test/integer_q:label')"/></input>
        """.strip()
        
        expected_integer_binding_xml = """
        <bind nodeset="/test/integer_q" type="int" required="true()"/>
        """.strip()
        
        q = create_survey_element_from_dict(simple_integer_question)
        
        self.s.add_child(q)
        
        self.assertEqual(ctw(q.xml_control()), expected_integer_control_xml)
        
        if TESTING_BINDINGS:
            self.assertEqual(ctw(q.xml_binding()), expected_integer_binding_xml)


    def test_simple_date_question_type_multilingual(self):
        """
        not sure how date questions should show up.
        """
        simple_date_question = {"text": {"f": "fd", "e": "ed"}, "type": "date", "name": "date_q", "attributes": {}}
        
        expected_date_control_xml = """
        <input ref="/test/date_q"><label ref="jr:itext('/test/date_q:label')"/></input>
        """.strip()
        
        expected_date_binding_xml = """
        <bind nodeset="/test/date_q" type="date" required="true()"/>
        """.strip()
        
        q = create_survey_element_from_dict(simple_date_question)
        self.s.add_child(q)
        self.assertEqual(ctw(q.xml_control()), expected_date_control_xml)
        
        if TESTING_BINDINGS:
            self.assertEqual(ctw(q.xml_binding()), expected_date_binding_xml)
    
    def test_simple_phone_number_question_type_multilingual(self):
        """
        not sure how phone number questions should show up.
        """
        simple_phone_number_question = {
            "label": {"f": "fe", "e": "ee"},
            "type": "phone number",
            "name": "phone_number_q",
            }

        expected_phone_number_control_xml = """<input ref="/test/phone_number_q"><label ref="jr:itext('/test/phone_number_q:label')"/><hint ref="jr:itext('/test/phone_number_q:hint')"/></input>"""

        expected_phone_number_binding_xml = """
        <bind required="true()" jr:constraintMsg="Please enter only numbers." nodeset="/test/phone_number_q" type="string" constraint="regex(., '^\d*$')"/>
        """.strip()
        
        q = create_survey_element_from_dict(simple_phone_number_question)
        self.s.add_child(q)
        self.assertEqual(ctw(q.xml_control()), expected_phone_number_control_xml)
        
        if TESTING_BINDINGS:
            self.assertEqual(ctw(q.xml_binding()), expected_phone_number_binding_xml)

    def test_simple_select_all_question_multilingual(self):
        """
        not sure how select all questions should show up...
        """
        simple_select_all_question = {
            "label": {"f": "f choisit", "e": "e choose"},
            "type": "select all that apply",
            "name": "select_all_q",
            "choices": [
                {"label": {"f": "ff", "e": "ef"}, "value": "f"},
                {"label": {"f": "fg", "e": "eg"}, "value": "g"},
                {"label": {"f": "fh", "e": "eh"}, "value": "h"}
                ]
            }

        expected_select_all_control_xml = """<select ref="/test/select_all_q"><label ref="jr:itext('/test/select_all_q:label')"/><hint ref="jr:itext('/test/select_all_q:hint')"/><item><label ref="jr:itext('/test/select_all_q/f:label')"/><value>f</value></item><item><label ref="jr:itext('/test/select_all_q/g:label')"/><value>g</value></item><item><label ref="jr:itext('/test/select_all_q/h:label')"/><value>h</value></item></select>"""
        
        expected_select_all_binding_xml = """
        <bind nodeset="/test/select_all_q" type="select" required="false()"/>
        """.strip()
        
        q = create_survey_element_from_dict(simple_select_all_question)
        self.s.add_child(q)
        self.assertEqual(ctw(q.xml_control()), expected_select_all_control_xml)
        
        if TESTING_BINDINGS:
            self.assertEqual(ctw(q.xml_binding()), expected_select_all_binding_xml)

    def test_simple_decimal_question_multilingual(self):
        """
        not sure how decimal should show up.
        """
        simple_decimal_question = {"text": {"f": "f text", "e": "e text"}, "type": "decimal", "name": "decimal_q", "attributes": {}}

        expected_decimal_control_xml = """
        <input ref="/test/decimal_q"><label ref="jr:itext('/test/decimal_q:label')"/></input>
        """.strip()
        
        expected_decimal_binding_xml = """
        <bind nodeset="/test/decimal_q" type="decimal" required="true()"/>
        """.strip()
        
        q = create_survey_element_from_dict(simple_decimal_question)
        self.s.add_child(q)
        self.assertEqual(ctw(q.xml_control()), expected_decimal_control_xml)
        
        if TESTING_BINDINGS:
            self.assertEqual(ctw(q.xml_binding()), expected_decimal_binding_xml)
