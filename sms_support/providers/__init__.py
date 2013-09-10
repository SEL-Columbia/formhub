#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from smssync import (import_submission as imp_sub_smssync,
                     import_submission_for_form as imp_sub_form_smssync,
                     autodoc as autodoc_smssync)
from telerivet import (import_submission as imp_sub_telerivet,
                       import_submission_for_form as imp_sub_form_telerivet,
                       autodoc as autodoc_telerivet)
from twilio import (import_submission as imp_sub_twilio,
                    import_submission_for_form as imp_sub_form_twilio,
                    autodoc as autodoc_twilio)
from textit import (import_submission as imp_sub_textit,
                    import_submission_for_form as imp_sub_form_textit,
                    autodoc as autodoc_textit)

SMSSYNC = 'smssync'
TELERIVET = 'telerivet'
TWILIO = 'twilio'
TEXTIT = 'textit'

PROVIDERS = {
    SMSSYNC: {'name': u"SMS Sync",
              'imp': imp_sub_smssync,
              'imp_form': imp_sub_form_smssync,
              'doc': autodoc_smssync},
    TELERIVET: {'name': u"Telerivet",
                'imp': imp_sub_telerivet,
                'imp_form': imp_sub_form_telerivet,
                'doc': autodoc_telerivet},
    TWILIO: {'name': u"Twilio",
             'imp': imp_sub_twilio,
             'imp_form': imp_sub_form_twilio,
             'doc': autodoc_twilio},
    TEXTIT: {'name': u"Text It",
             'imp': imp_sub_textit,
             'imp_form': imp_sub_form_textit,
             'doc': autodoc_textit}
}


def unknown_service(request, username=None, id_string=None):
    """ 400 view for request with unknown service name """
    r = HttpResponse(u"Unknown SMS Gateway Service", mimetype='text/plain')
    r.status_code = 400
    return r


@csrf_exempt
def import_submission(request, username, service):
    """ Proxy to the service's import_submission view """
    return PROVIDERS.get(service.lower(), {}) \
                    .get('imp', unknown_service)(request, username)


@csrf_exempt
def import_submission_for_form(request, username, id_string, service):
    """ Proxy to the service's import_submission_for_form view """
    return PROVIDERS.get(service.lower(), {}) \
                    .get('imp_form', unknown_service)(request, username, id_string)


def providers_doc(url_root, username, id_string):
    return [{'id': pid,
             'name': p.get('name'),
             'doc': p.get('doc')(url_root, username, id_string)}
            for pid, p in PROVIDERS.items()]
