from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.utils import simplejson

def phone_manager(request):
    info={'user':request.user}
    return render_to_response("phone_manager.html", info)

def phone_manager_json(request):
    phonet = {}
    phonet['columns'] = [{'name':'Registered To', 'id':'surveyor'}, \
                    {'name':'Status','id':'status'}, {'name':'Notes','id':'notes'}, \
                    {'name':'Visible ID','id':'external_id'}, {'name':'Current Number','id':'phone_number'}]
                    
    phonet['rows'] = [
    {'surveyor':'Bob', 'status':'functional','notes':None, 'external_id':'001', 'phone_number':'609.902.4682'}, \
    {'surveyor':'Sven', 'status':'functional','notes':None, 'external_id':'023', 'phone_number':'609.902.4681'}, \
    {'surveyor':'Wynonah', 'status':'functional','notes':None, 'external_id':'024', 'phone_number':'609.902.4683'}, \
    {'surveyor':None, 'status':'broken','notes':'GPS Broken', 'external_id':'007', 'phone_number':'609.902.4685'} \
    ]
    return HttpResponse(simplejson.dumps(phonet))