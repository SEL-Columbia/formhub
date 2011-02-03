from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.utils import simplejson

def phone_manager(request):
    info={'user':request.user}
    return render_to_response("phone_manager.html", info)

def phone_manager_json(request):
    return HttpResponse(simplejson.dumps({'message':'hello'}))