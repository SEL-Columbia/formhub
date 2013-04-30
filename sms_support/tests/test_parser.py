#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

# from django.core.urlresolvers import reverse
from test_base import TestBase
from sms_support.tools import (SMS_API_ERROR, SMS_PARSING_ERROR,
                               SMS_SUBMISSION_ACCEPTED,
                               SMS_SUBMISSION_REFUSED)


class TestParser(TestBase):

    def setUp(self):
        TestBase.setUp(self)
        self.setup_form(allow_sms=True)

    def test_api_error(self):
        # missing identity or text
        result = self.response_for_text(self.username, 'hello', identity='')
        self.assertEqual(result['code'], SMS_API_ERROR)

        result = self.response_for_text(self.username, text='')
        self.assertEqual(result['code'], SMS_API_ERROR)

    def test_invalid_syntax(self):
        # invalid text message
        result = self.response_for_text(self.username, 'hello')
        self.assertEqual(result['code'], SMS_PARSING_ERROR)

    def test_invalid_group(self):
        # invalid text message
        result = self.response_for_text(self.username, '++a 20',
                                        id_string=self.id_string)
        self.assertEqual(result['code'], SMS_PARSING_ERROR)

    def test_refused_with_keyword(self):
        # submission has proper keywrd with invalid text
        result = self.response_for_text(self.username, 'test allo')
        self.assertEqual(result['code'], SMS_PARSING_ERROR)

    def test_sucessful_submission(self):
        result = self.response_for_text(self.username,
                                        'test +a 1 y 1950-02-22 john doe')
        self.assertEqual(result['code'], SMS_SUBMISSION_ACCEPTED)
        self.assertTrue(result['id'])

    def test_invalid_type(self):
        result = self.response_for_text(self.username,
                                        'test +a yes y 1950-02-22 john doe')
        self.assertEqual(result['code'], SMS_PARSING_ERROR)

    def test_missing_required_field(self):
        # required field name missing
        result = self.response_for_text(self.username,
                                        'test +b ff')
        self.assertEqual(result['code'], SMS_SUBMISSION_REFUSED)
