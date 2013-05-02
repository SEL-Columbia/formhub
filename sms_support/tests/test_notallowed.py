#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from test_base import TestBase
from sms_support.tools import SMS_SUBMISSION_REFUSED


class TestNotAllowed(TestBase):

    def setUp(self):
        TestBase.setUp(self)
        self.setup_form(allow_sms=False)

    def test_refused_not_enabled(self):
        # SMS submissions not allowed
        result = self.response_for_text(self.username, 'test allo')
        self.assertEqual(result['code'], SMS_SUBMISSION_REFUSED)

    def test_allow_sms(self):
        result = self.response_for_text(self.username,
                                        'test +a 1 y 1950-02-22 john doe')
        self.assertEqual(result['code'], SMS_SUBMISSION_REFUSED)
        self.assertEqual(result.get('id'), None)
