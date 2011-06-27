from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.http import HttpResponse

def dashboard(request, reqpath):
    if request.method == "POST":
        geoid = request.POST['lga']
        if LGA.objects.filter(geoid=geoid).count() > 0:
            return HttpResponseRedirect("/ui/%s" % geoid)
    context = RequestContext(request)
    lga = None
    context.active_districts = active_districts()
    if not reqpath == "":
        try:
            lga = LGA.objects.get(geoid=reqpath)
        except:
            lga = None
        if lga == None:
            return HttpResponseRedirect("/ui/")
    if lga == None:
        return country_view(context)
    else:
        context.lga = lga
        return lga_view(context)

def country_view(context):
    context.site_title = "Nigeria"
    return render_to_response("ui.html", context_instance=context)

def lga_view(context):
    context.site_title = "LGA View"
    context.lga_id = context.lga.geoid
    return render_to_response("ui.html", context_instance=context)

from facility_views.models import FacilityTable

def variable_data(request):
    sectors = []
    for sector_table in FacilityTable.objects.all():
        sectors.append(sector_table.display_dict())
    import json
    return HttpResponse(json.dumps({
        'sectors': sectors
    }))

from django.db.models import Count
from nga_districts.models import LGA
def active_districts():
    lgas = LGA.objects.annotate(facility_count=Count('facilities')).filter(facility_count__gt=0)
    lga_list = []
    from collections import defaultdict
    states = defaultdict(list)
    for lga in lgas:
        states[lga.state].append(lga)
    for state, lgas in states.items():
        for lga in lgas:
            lga_list.append(
                (lga.geoid, lga.state.name, lga.name)
                )
    return lga_list