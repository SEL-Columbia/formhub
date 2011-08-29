# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response

from django.db.models import Count
from nga_districts.models import LGA


def index(request):
    context = RequestContext(request)
    context.extra_links = 'publish_link.html'
    return render_to_response("survey_list.html", context_instance=context)


def publish(request, id_string):
    pass


def list_active_lgas(request):
    context = RequestContext(request)
    context.site_title = "NMIS: LGA List"
    context.lgas = LGA.objects.annotate(facility_count=Count('facilities')).filter(facility_count__gt=0)
    return render_to_response("list_active_lgas.html", context_instance=context)

def site_description(request):
    return render_to_response("site_description.html")

def baseline_redirect(request):
    return HttpResponseRedirect("/baseline/")
