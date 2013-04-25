#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

""" Twilio SMS gateway

    Supports Receiving and replying SMS from/to Twilio.
    URL must be set to POST method in Twilio.

    See: http://www.twilio.com/docs/api/twiml/sms/twilio_request
         http://www.twilio.com/docs/api/twiml/sms/your_response """

# import json
import datetime

from dict2xml import dict2xml
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import ugettext as _

from sms_support.tools import SMS_API_ERROR, SMS_SUBMISSION_ACCEPTED
from sms_support.parser import process_incoming_smses


def get_response(data):

    xml_head = u'<?xml version="1.0" encoding="UTF-8" ?>'
    response_dict = {'Response': {}}
    message = data.get('text')

    if data.get('code') == SMS_API_ERROR:
        message = None
    elif data.get('code') != SMS_SUBMISSION_ACCEPTED:
        message = _(u"[ERROR] %s") % message

    if message:
        response_dict.update({"Response": {'Sms': message}})

    response = xml_head + dict2xml(response_dict)
    return HttpResponse(response, mimetype='text/xml')


@require_POST
@csrf_exempt
def import_submission(request, username):
    """ Proxy to import_submission_for_form with None as id_string """

    return import_submission_for_form(request, username, None)


@require_POST
@csrf_exempt
def import_submission_for_form(request, username, id_string):
    """ Retrieve and process submission from SMSSync Request """

    sms_identity = request.POST.get('From', '').strip()
    sms_text = request.POST.get('Body', '').strip()
    now_timestamp = datetime.datetime.now().strftime('%s')
    sent_timestamp = request.POST.get('time_created', now_timestamp).strip()
    try:
        sms_time = datetime.datetime.fromtimestamp(float(sent_timestamp))
    except ValueError:
        sms_time = datetime.datetime.now()

    return process_message_for_twilio(username=username,
                                      sms_identity=sms_identity,
                                      sms_text=sms_text,
                                      sms_time=sms_time,
                                      id_string=id_string)


def process_message_for_twilio(username,
                               sms_identity, sms_text, sms_time, id_string):
    """ Process a text instance and return in SMSSync expected format """

    if not sms_identity or not sms_text:
        return get_response({'code': SMS_API_ERROR,
                             'text': _(u"`identity` and `message` are "
                                       u"both required and must not be "
                                       u"empty.")})

    incomings = [(sms_identity, sms_text)]
    response = process_incoming_smses(username, incomings, id_string)[-1]

    return get_response(response)
