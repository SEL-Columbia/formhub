# Create your views here.
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
import json

from nga_districts.models import LGA
from facilities.models import Facility


def home(request):
    context = RequestContext(request)
    context.sites = LGA.objects.all()
    return render_to_response("list_lgas.html", context_instance=context)


def facilities_for_site(request, site_id):
    lga = LGA.objects.get(slug=site_id)
    return HttpResponse(json.dumps(Facility.get_latest_data_by_lga(lga)))


def facility(request, facility_id):
    """
    Return the latest information we have on this facility.
    """
    facility = Facility.objects.get(id=facility_id)
    text = json.dumps(facility.get_latest_data(), indent=4, sort_keys=True)
    return HttpResponse(text)
