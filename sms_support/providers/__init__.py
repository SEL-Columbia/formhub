#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from smssync import (import_submission as imp_sub_smssync,
                     import_submission_for_form as imp_sub_form_smssync)
from telerivet import (import_submission as imp_sub_telerivet,
                       import_submission_for_form as imp_sub_form_telerivet)
from twilio import (import_submission as imp_sub_twilio,
                    import_submission_for_form as imp_sub_form_twilio)

SMSSYNC = 'smssync'
TELERIVET = 'telerivet'
TWILIO = 'twilio'

IMP_FUNC = {
    SMSSYNC: imp_sub_smssync,
    TELERIVET: imp_sub_telerivet,
    TWILIO: imp_sub_twilio
}

IMP_FORM_FUNC = {
    SMSSYNC: imp_sub_form_smssync,
    TELERIVET: imp_sub_form_telerivet,
    TWILIO: imp_sub_form_twilio
}


def unknown_service(request, username=None, id_string=None):
    """ 400 view for request with unknown service name """
    r = HttpResponse(u"Unknown SMS Gateway Service", mimetype='text/plain')
    r.status_code = 400
    return r


@csrf_exempt
def import_submission(request, username, service):
    """ Proxy to the service's import_submission view """
    return IMP_FUNC.get(service.lower(), unknown_service)(request, username)


@csrf_exempt
def import_submission_for_form(request, username, id_string, service):
    """ Proxy to the service's import_submission_for_form view """
    return IMP_FORM_FUNC.get(service.lower(),
                             unknown_service)(request, username, None)
