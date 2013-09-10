#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import json

from django.http import HttpResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import ugettext as _

from tools import SMS_API_ERROR
from parser import process_incoming_smses


def get_response(data):
    response = {'status': data.get('code'),
                'message': data.get('text')}
    return HttpResponse(json.dumps(response), mimetype='application/json')


@require_GET
def import_submission(request, username):
    """ Process an SMS text as a form submission

    :param string identity: phone number of the sender
    :param string text: SMS content

    :returns: a JSON dict with:
        'status': one of 'ACCEPTED', 'REJECTED', 'PARSING_FAILED'
        'message': Error message if not ACCEPTED.
        'id: Unique submission ID if ACCEPTED. """

    return import_submission_for_form(request, username, None)


@require_POST
@csrf_exempt
def import_multiple_submissions(request, username):
    ''' Process several POSTED SMS texts as XForm submissions

        :param json messages: JSON list of {"identity": "x", "text": "x"}
        :returns json list of
            {"status": "x", "message": "x", "id": "x"} '''

    return import_multiple_submissions_for_form(request, username, None)


@require_GET
def import_submission_for_form(request, username, id_string):
    """ idem import_submission with a defined id_string """

    sms_identity = request.GET.get('identity', '').strip()
    sms_text = request.GET.get('text', '').strip()

    if not sms_identity or not sms_text:
        return get_response({'code': SMS_API_ERROR,
                             'text': _(u"`identity` and `message` are "
                                       u"both required and must not be "
                                       u"empty.")})
    incomings = [(sms_identity, sms_text)]
    response = process_incoming_smses(username, incomings, id_string)[-1]

    return get_response(response)


@require_POST
@csrf_exempt
def import_multiple_submissions_for_form(request, username, id_string):
    """ idem import_multiple_submissions with a defined id_string """

    messages = json.loads(request.POST.get('messages', '[]'))
    incomings = [(m.get('identity', ''), m.get('text', '')) for m in messages]

    responses = [{'status': d.get('code'),
                  'message': d.get('text'),
                  'instanceID': d.get('id')} for d
                 in process_incoming_smses(username, incomings, id_string)]

    return HttpResponse(json.dumps(responses), mimetype='application/json')
