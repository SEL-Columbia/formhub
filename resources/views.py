# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response

def resources(request):
    context = RequestContext(request)
    return render_to_response("resources.html", context_instance=context)
