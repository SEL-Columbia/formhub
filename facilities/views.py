# Create your views here.
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
import json

from facilities.models import *

def home(request):
    context = RequestContext(request)
    context.sites = LGA.objects.all()
    return render_to_response("list_lgas.html", context_instance=context)

def facilities_for_site(request, site_id):
    sample_data = [
        {'uid': 1,
        'name': 'Some name',
        'latlng': [12.234, 42.567],
        'sector': 'water'},
        {'uid': 2,
        'name': 'Another name',
        'sector': 'education',
        'latlng': [12.21, 42.222]},
        {'uid': 3,
        'name': 'And another name',
        'sector': 'health',
        'latlng': [12.45, 42.34]}
    ]
    return HttpResponse(json.dumps(sample_data))
#    context = RequestContext(request)
#    lga = LGA.objects.get(slug=site_id)
#    return HttpResponse(json.dumps(Facility.get_latest_data_by_lga(lga)))
