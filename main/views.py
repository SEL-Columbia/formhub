# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response

def index(request):
    context = RequestContext(request)
    return render_to_response("main_index.html", context_instance=context)

def baseline_redirect(request):
    return HttpResponseRedirect("/baseline/")