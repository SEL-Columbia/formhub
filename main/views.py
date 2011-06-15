# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.http import HttpResponseRedirect

def baseline_redirect(request):
    return HttpResponseRedirect("/baseline/")