#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

from django.shortcuts import render_to_response
from django.http import (HttpResponse, HttpResponseBadRequest, 
                         HttpResponseRedirect)
                         
from django.forms.models import model_to_dict

from odk_dropbox.models import Phone, Surveyor
                         
try:
    import json
except ImportError:
    from django.utils import simplejson as json


def phone_manager(request):
    info={'user':request.user}
    return render_to_response("phone_manager.html", info)


def phone_manager_json(request):
    """
        Send a list of phones with their attributes and status.
    """

    phonet = {}

    phones_dicts = []
    for phone in Phone.objects.all():
        phone = model_to_dict(phone)
        phone['surveyor'] = Surveyor.objects.get(id=phone['surveyor']).name
        phones_dicts.append(phone)
    
    phonet['rows'] = phones_dicts
        
    # set a mapping to for the client side to match ids with the column name
    phonet['columns'] = [{'name': f.verbose_name, 
                         'id': f.attname} for f in Phone._meta.fields]
                    
    return HttpResponse(json.dumps(phonet),
                        mimetype='application/json')
