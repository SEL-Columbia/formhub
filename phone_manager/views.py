#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

from django.shortcuts import render_to_response
from django.http import (HttpResponse, HttpResponseBadRequest, 
                         HttpResponseRedirect)
                         
try:
    import json
except ImportError:
    from django.utils import simplejson as json

from django.core import serializers


def phone_manager(request):
    info={'user':request.user}
    return render_to_response("phone_manager.html", info)


def phone_manager_json(request):
    """
        Send a list of phones with their attributes and status.
    """

    phonet = {}

    phones = Phone.objects.all()
    phones_json = serializers.serialize('json', phones,  ensure_ascii=False)
    
    # replace the surveyor id by his name
    for phone in phones_json:
        phone['surveyor'] = Surveyor.object.get(id=phone['surveyor']).name

    phonet['rows'] = phones_json
        
    # set a mapping to for the client side to match ids with the column name
    
    
    phonet['columns'] = [{'name': f.verbose_name, 
                         'id': f.attname} for f in Phone._meta.fields]
                    
    return HttpResponse(json.dumps(phonet),
                        mimetype='application/json')
