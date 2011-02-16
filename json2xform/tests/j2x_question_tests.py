"""
Testing creation of Surveys using verbose methods
"""
import sys, os

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.test import TestCase, Client
from .json2xform import *

import json

from ..utils import E, ns, etree

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
                    "type": "string", "name": "enumerator_name"}

        q = create_question_from_dict(simple_string_json)
        self.s._add_element(q)
        self.assertEqual(ctw(q.control()), \
                "<input ref=\"/test/enumerator_name\"><label ref=\"jr:itext('q_enumerator_name')\"/></input>")
    
    def test_select_one_question_multilingual(self):
        """
        Test the lowest common denominator of question types.
        """
        simple_select_one_json = {"text": {"f": "ftext","e": "etext"},\
                "type": "select one","name": "qname","choices": \
                [{"text": {"f": "fa","e": "ea"},"value": "a"}, \
                {"text": {"f": "fb","e": "eb"},"value": "b"}]}

        q = create_question_from_dict(simple_select_one_json)
        self.s._add_element(q)
        self.assertEqual(ctw(q.control()), '<select1 ref="/test/qname"><label ref="jr:itext(\'q_qname\')"/></select1>')

    def test_simple_integer_question_type_multilingual(self):
        """
        not sure how integer questions should show up.
        """
        simple_integer_question = {"text": {"f": "fc", "e": "ec"}, "type": "integer", "name": "integer_q", "attributes": {}}
        
        q = create_question_from_dict(simple_integer_question)
        self.s._add_element(q)
        self.assertEqual(ctw(q.control()), '?')


    def test_simple_date_question_type_multilingual(self):
        """
        not sure how date questions should show up.
        """
        simple_date_question = {"text": {"f": "fd", "e": "ed"}, "type": "date", "name": "date_q", "attributes": {}}
        
        q = create_question_from_dict(simple_date_question)
        self.s._add_element(q)
        self.assertEqual(ctw(q.control()), '?')


    def test_simple_phone_number_question_type_multilingual(self):
        """
        not sure how phone number questions should show up.
        """
        simple_integer_question = {"text": {"f": "fe", "e": "ee"}, "type": "phone number", "name": "phone_number_q", "attributes": {}}

        q = create_question_from_dict(simple_integer_question)
        self.s._add_element(q)
        self.assertEqual(ctw(q.control()), '?')

    def test_simple_select_all_question_multilingual(self):
        """
        not sure how select all questions should show up...
        """
        simple_select_all_question = {"text": {"f": "f choisit", "e": "e choose"}, "attributes": {}, "type": "select all that apply", "name": "select_all_q", "choices": [{"text": {"f": "ff", "e": "ef"}, "value": "f"}, {"text": {"f": "fg", "e": "eg"}, "value": "g"}, {"text": {"f": "fh", "e": "eh"}, "value": "h"}]}
        
        q = create_question_from_dict(simple_select_all_question)
        self.s._add_element(q)
        self.assertEqual(ctw(q.control()), '?')

    def test_simple_decimal_question_multilingual(self):
        """
        not sure how decimal should show up.
        """
        simple_decimal_question = {"text": {"f": "f text", "e": "e text"}, "type": "decimal", "name": "decimal_q", "attributes": {}}
        
        q = create_question_from_dict(simple_decimal_question)
        self.s._add_element(q)
        self.assertEqual(ctw(q.control()), '?')
