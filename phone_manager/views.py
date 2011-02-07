#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.shortcuts import render_to_response
from django.http import (HttpResponse, HttpResponseBadRequest, 
                         HttpResponseRedirect)

# update_object and ModelForm are used to update phone status
from django.views.generic.create_update import update_object
from django.forms import ModelForm
                         
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
    
    phones = Phone.objects.all()

    search = request.GET.get('search', '')
    if search.strip():
        terms = search.split()
        for term in terms:
            phones = phones.filter(search_field__contains=term)

    paginator = Paginator(phones, 50, orphans=10, 
                          allow_empty_first_page=True)

    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    try:
        phones_page = paginator.page(page)
    except (EmptyPage, InvalidPage):
        phones_page = paginator.page(paginator.num_pages)

    # add pagination information
    next = phones_page.next_page_number() if phones_page.has_next() else -1
    prev = phones_page.previous_page_number() if phones_page.has_previous() else -1
    phonet['pagination'] = {'phone_count': paginator.count, 
                            'page_count': paginator.num_pages,
                            'next_page': next,
                            'previous_page': prev,
                            'page': page}
    
    #when there's a search query, pass it back to the page in the json
    phonet['search_error'] = "We could not find the record you were looking for."
    
    # turn phones into a dict with surveroy id replace by it's name
    phones_dicts = []
    for phone in phones_page.object_list:
        phone = model_to_dict(phone)
        try:
            phone['surveyor_id'] = Surveyor.objects.get(id=phone['surveyor']).name
        except:
            phone['surveyor_id'] = "No Surveyor Found"
        phones_dicts.append(phone)
    
    phonet['rows'] = phones_dicts
        
    # set a mapping to for the client side to match ids with the column name
    fields = []
    for f in Phone._meta.fields:
        if f.attname != "search_field":
            fields.append({'name': f.verbose_name, 'id': f.attname})
    phonet['columns'] = fields
                    
    return HttpResponse(json.dumps(phonet),
                        mimetype='application/json')

class PhoneForm(ModelForm):
    class Meta:
        model = Phone
        exclude = ('imei',)

def update_phone(request, phone_id):
    return update_object(
        request=request,
        object_id=phone_id,
        form_class=PhoneForm,
        template_name="phone_form.html",
        )
