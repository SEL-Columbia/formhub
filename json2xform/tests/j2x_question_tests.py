"""
Testing creation of Surveys using verbose methods
"""
import sys, os

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.test import TestCase, Client
from json2xform import *
from json2xform.question import create_question_from_dict

import json

from ..utils import E, ns, etree

TESTING_BINDINGS = False

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
        simple_string_json = {"text": {"French": "Nom du travailleur agricole:", \
                    "English": "Name of Community Agricultural Worker"}, \
                    "type": "text", "name": "enumerator_name"}

        q = create_question_from_dict(simple_string_json)
        
        expected_string_control_xml = """
        <input ref="/test/enumerator_name"><label ref="jr:itext('q_enumerator_name')"/></input>
        """.strip()
        
        expected_string_binding_xml = """
        <bind nodeset="/test/enumerator_name" type="string" />
        """.strip()
        
        self.s._add_element(q)
        self.assertEqual(ctw(q.control()), expected_string_control_xml)
        
        if TESTING_BINDINGS:
            self.assertEqual(ctw(q.get_bindings()), expected_string_binding_xml)
    
    def test_select_one_question_multilingual(self):
        """
        Test the lowest common denominator of question types.
        """
        simple_select_one_json = {"text": {"f": "ftext","e": "etext"},\
                "type": "select one","name": "qname","choices": \
                [{"text": {"f": "fa","e": "ea"},"value": "a"}, \
                {"text": {"f": "fb","e": "eb"},"value": "b"}]}
        
        expected_select_one_control_xml = """NOT CORRECT
        <select1 ref="/test/qname"><label ref="jr:itext('q_qname')"/></select1>
        """.strip()
        
        expected_select_one_binding_xml = """
        <bind nodeset="/test/qname" type="select1"/>
        """.strip()
        
        q = create_question_from_dict(simple_select_one_json)
        self.s._add_element(q)
        self.assertEqual(ctw(q.control()), expected_select_one_control_xml)
        
        if TESTING_BINDINGS:
            self.assertEqual(ctw(q.get_bindings()), expected_select_one_binding_xml)

    def test_simple_integer_question_type_multilingual(self):
        """
        not sure how integer questions should show up.
        """
        simple_integer_question = {"text": {"f": "fc", "e": "ec"}, "type": "integer", "name": "integer_q", "attributes": {}}

        expected_integer_control_xml = """
        <input ref="/test/integer_q"><label ref="jr:itext('q_integer_q')"/></input>
        """.strip()
        
        expected_integer_binding_xml = """
        <bind nodeset="/test/integer_q" type="int"/>
        """.strip()
        
        q = create_question_from_dict(simple_integer_question)
        
        self.s._add_element(q)
        
        self.assertEqual(ctw(q.control()), expected_integer_control_xml)
        
        if TESTING_BINDINGS:
            self.assertEqual(ctw(q.get_bindings()), expected_integer_binding_xml)


    def test_simple_date_question_type_multilingual(self):
        """
        not sure how date questions should show up.
        """
        simple_date_question = {"text": {"f": "fd", "e": "ed"}, "type": "date", "name": "date_q", "attributes": {}}
        
        expected_date_control_xml = """
        <input ref="/test/date_q"><label ref="jr:itext('q_date_q')"/></input>
        """.strip()
        
        expected_date_binding_xml = """
        <bind nodeset="/test/date_q" type="date"/>
        """.strip()
        
        q = create_question_from_dict(simple_date_question)
        self.s._add_element(q)
        self.assertEqual(ctw(q.control()), expected_date_control_xml)
        
        if TESTING_BINDINGS:
            self.assertEqual(ctw(q.get_bindings()), expected_date_binding_xml)
    
    def test_simple_phone_number_question_type_multilingual(self):
        """
        not sure how phone number questions should show up.
        """
        simple_phone_number_question = {"text": {"f": "fe", "e": "ee"}, "type": "phone number", "name": "phone_number_q", "attributes": {}}

        expected_phone_number_control_xml = """PROBABLY WANT A HINT IN HERE
        <input ref="/test/phone_number_q"><label ref="jr:itext('q_phone_number_q')"/></input>
        """.strip()

        expected_phone_number_binding_xml = """MAYBE WANT A CONSTRAINT MESSAGE
        <bind nodeset="/test/phone_number_q" type="string" constraint="regex(., '^\d*$')"/>
        """.strip()
        
        q = create_question_from_dict(simple_phone_number_question)
        self.s._add_element(q)
        self.assertEqual(ctw(q.control()), expected_phone_number_control_xml)
        
        if TESTING_BINDINGS:
            self.assertEqual(ctw(q.get_bindings()), expected_phone_number_binding_xml)

    def test_simple_select_all_question_multilingual(self):
        """
        not sure how select all questions should show up...
        """
        simple_select_all_question = {"text": {"f": "f choisit", "e": "e choose"}, "attributes": {}, "type": "select all that apply", "name": "select_all_q", "choices": [{"text": {"f": "ff", "e": "ef"}, "value": "f"}, {"text": {"f": "fg", "e": "eg"}, "value": "g"}, {"text": {"f": "fh", "e": "eh"}, "value": "h"}]}

        expected_select_all_control_xml = """NEED ITEMS LIST HERE
        <select ref="/test/select_all_q"><label ref="jr:itext('q_select_all_q')"/></select>
        """.strip()
        
        expected_select_all_binding_xml = """DEFINITELY WANT TO MAKE THIS REQUIRED WITH A NONE OPTION AVAILABLE
        <bind nodeset="/test/select_all_q" type="select" required="false()"/>
        """.strip()
        
        q = create_question_from_dict(simple_select_all_question)
        self.s._add_element(q)
        self.assertEqual(ctw(q.control()), expected_select_all_control_xml)
        
        if TESTING_BINDINGS:
            self.assertEqual(ctw(q.get_bindings()), expected_select_all_binding_xml)

    def test_simple_decimal_question_multilingual(self):
        """
        not sure how decimal should show up.
        """
        simple_decimal_question = {"text": {"f": "f text", "e": "e text"}, "type": "decimal", "name": "decimal_q", "attributes": {}}

        expected_decimal_control_xml = """
        <input ref="/test/decimal_q"><label ref="jr:itext('q_decimal_q')"/></input>
        """.strip()
        
        expected_decimal_binding_xml = """
        <bind nodeset="/test/decimal_q" type="decimal"/>
        """.strip()
        
        q = create_question_from_dict(simple_decimal_question)
        self.s._add_element(q)
        self.assertEqual(ctw(q.control()), expected_decimal_control_xml)
        
        if TESTING_BINDINGS:
            self.assertEqual(ctw(q.get_bindings()), expected_decimal_binding_xml)
