#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

""" Ushaidi's SMSSync gateway

    Supports Receiving and replying SMS from/to the SMSSync App.

    See: http://smssync.ushahidi.com/doc """

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
                                      'service': 'smssync'})
    urlb = url_root + reverse('sms_submission_form_api',
                              kwargs={'username': username,
                                      'id_string': id_string,
                                      'service': 'smssync'})
    doc = (u'<p>' +
           _(u"%(service)s Instructions:")
           % {'service': u'<a href="http://smssync.ushahidi.com/">'
                         u'Ushaidi\'s SMS Sync</a>'}
           + u'</p><ol><li>' +
           _(u"Download the SMS Sync App on your phone serving as a gateway.")
           + '</li><li>' +
           _(u"Configure the app to point to one of the following URLs")
           + u'<br /><span class="sms_autodoc_example">%(urla)s'
           + u'<br />%(urlb)s</span><br />' +
           _(u"Optionnaly set a keyword to prevent non-formhub "
             u"messages to be sent.")
           + '</li><li>' +
           _(u"In the preferences, tick the box to allow "
             u"replies from the server.")
           + '</li></ol><p>' +
           _(u"That's it. Now Send an SMS Formhub submission to the number "
             u"of that phone. It will create a submission on Formhub.")
           + u'</p>') % {'urla': urla, 'urlb': urlb}
    return doc


def get_response(data):
    message = data.get('text')
    if data.get('code') == SMS_API_ERROR:
        success = False
        message = None
    elif data.get('code') != SMS_SUBMISSION_ACCEPTED:
        success = True
        message = _(u"[ERROR] %s") % message
    else:
        success = True

    response = {
        "payload": {
            "success": success,
            "task": "send"}}

    if message:
        response['payload'].update({"messages": [{"to": data.get('identity'),
                                                  "message": message}]})
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

    sms_identity = request.POST.get('from', '').strip()
    sms_text = request.POST.get('message', '').strip()
    now_timestamp = datetime.datetime.now().strftime('%s')
    sent_timestamp = request.POST.get('sent_timestamp', now_timestamp).strip()
    try:
        sms_time = datetime.datetime.fromtimestamp(float(sent_timestamp))
    except ValueError:
        sms_time = datetime.datetime.now()

    return process_message_for_smssync(username=username,
                                       sms_identity=sms_identity,
                                       sms_text=sms_text,
                                       sms_time=sms_time,
                                       id_string=id_string)


def process_message_for_smssync(username,
                                sms_identity, sms_text, sms_time, id_string):
    """ Process a text instance and return in SMSSync expected format """

    if not sms_identity or not sms_text:
        return get_response({'code': SMS_API_ERROR,
                             'text': _(u"`identity` and `message` are "
                                       u"both required and must not be "
                                       u"empty.")})

    incomings = [(sms_identity, sms_text)]
    response = process_incoming_smses(username, incomings, id_string)[-1]
    response.update({'identity': sms_identity})

    return get_response(response)
