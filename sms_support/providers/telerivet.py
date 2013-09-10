#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

""" Telerivet WebHook gateway

    Supports Receiving and replying SMS from/to Telerivet Service

    See: http://telerivet.com/help/api/webhook/receiving """

import json
import datetime

from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import ugettext as _

from sms_support.tools import SMS_API_ERROR, SMS_SUBMISSION_ACCEPTED
from sms_support.parser import process_incoming_smses


def autodoc(url_root, username, id_string):
    urla = url_root + reverse('sms_submission_api',
                              kwargs={'username': username,
                                      'service': 'telerivet'})
    urlb = url_root + reverse('sms_submission_form_api',
                              kwargs={'username': username,
                                      'id_string': id_string,
                                      'service': 'telerivet'})
    doc = (u'<p>' +
           _(u"%(service)s Instructions:")
           % {'service': u'<a href="https://telerivet.com">'
                         u'Telerivet\'s Webhook API</a>'}
           + u'</p><ol><li>' +
           _(u"Sign in to Telerivet.com and go to Service Page.")
           + u'</li><li>' +
           _(u"Follow instructions to add an application with either URL:")
           + u'<br /><span class="sms_autodoc_example">%(urla)s'
           + u'<br />%(urlb)s</span><br />'
           + u'</li></ol><p>' +
           _(u"That's it. Now Send an SMS Formhub submission to your Telerivet"
             u" phone number. It will create a submission on Formhub.")
           + u'</p>') % {'urla': urla, 'urlb': urlb}
    return doc


def get_response(data):

    message = data.get('text')

    if data.get('code') == SMS_API_ERROR:
        message = None
    elif data.get('code') != SMS_SUBMISSION_ACCEPTED:
        message = _(u"[ERROR] %s") % message

    response = {}

    if message:
        response.update({"messages": [{"content": message}]})
    return HttpResponse(json.dumps(response), mimetype='application/json')


@require_POST
@csrf_exempt
def import_submission(request, username):
    """ Proxy to import_submission_for_form with None as id_string """

    return import_submission_for_form(request, username, None)


@require_POST
@csrf_exempt
def import_submission_for_form(request, username, id_string):
    """ Retrieve and process submission from SMSSync Request """

    sms_identity = request.POST.get('from_number', '').strip()
    sms_text = request.POST.get('content', '').strip()
    now_timestamp = datetime.datetime.now().strftime('%s')
    sent_timestamp = request.POST.get('time_created', now_timestamp).strip()
    try:
        sms_time = datetime.datetime.fromtimestamp(float(sent_timestamp))
    except ValueError:
        sms_time = datetime.datetime.now()

    return process_message_for_telerivet(username=username,
                                         sms_identity=sms_identity,
                                         sms_text=sms_text,
                                         sms_time=sms_time,
                                         id_string=id_string)


def process_message_for_telerivet(username,
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
