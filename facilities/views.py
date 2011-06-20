# Create your views here.
from django.shortcuts import render_to_response
from django.template import RequestContext
import json

from facilities.models import *

def home(request):
    context = RequestContext(request)
    context.sites = LGA.objects.all()
    return render_to_response("sites.html", context_instance=context)

def facilities_for_site(request, site_id):
    context = RequestContext(request)
    lga = LGA.objects.get(slug=site_id)
    context.site = lga
    context.site_name = lga.name
    context.ftypes = list(FacilityType.objects.all())
    context.facility_data = json.dumps(Facility.get_latest_data_by_lga(lga))
    return render_to_response("facilities_by_lga.html", context_instance=context)
