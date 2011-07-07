# Create your views here.
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
import json

from nga_districts.models import LGA
from facilities.models import Facility, FacilityRecord, Variable


def home(request):
    context = RequestContext(request)
    context.sites = LGA.objects.all()
    return render_to_response("list_lgas.html", context_instance=context)


def data_dictionary(request):
    return HttpResponse(Variable.get_full_data_dictionary())


def facilities_for_site(request, site_id):
    def non_null(val_arr):
        #each datarecord should have at least 2 null values (out of 3)
        #this function returns the non-null value, if it exists.
        nns = []
        for v in val_arr:
            if v is not None:
                nns.append(v)
        assert len(nns) < 2
        if len(nns) == 0:
            #there were 3 null values
            return None
        else:
            #there was 1 non-null value
            return nns[0]
    lga = LGA.objects.get(unique_slug=site_id)
    facility_ids = [z['id'] for z in Facility.objects.filter(lga=lga).values('id')]
    d = {}
    drq = FacilityRecord.objects.order_by('-date')
    for facility in facility_ids:
        drs = drq.filter(facility=facility)
        dvals = {}
        #TODO: find something to fix the date problem.
        # (i think a different date would just override the entry in the dict)
        for t in drs.values('variable_id', 'string_value', 'float_value', 'boolean_value', 'date'):
            dvals[t['variable_id']] = \
                    non_null([t['string_value'], t['float_value'], t['boolean_value']])
        d[facility] = dvals
    oput = {
        'facilities': d,
        'lgaName': lga.name,
        'stateName': lga.state.name,
        'profileData': lga.get_latest_data(),
    }
    return HttpResponse(json.dumps(oput))


def facility(request, facility_id):
    """
    Return the latest information we have on this facility.
    """
    facility = Facility.objects.get(id=facility_id)
    text = json.dumps(facility.get_latest_data(), indent=4, sort_keys=True)
    return HttpResponse(text)


def boolean_counts_for_facilities_in_lga(request, lga_id):
    lga = LGA.objects.get(id=lga_id)
    text = json.dumps(FacilityRecord.counts_of_boolean_variables(lga), indent=4, sort_keys=True)
    return HttpResponse(text)
