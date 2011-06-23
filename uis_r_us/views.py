from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.http import HttpResponse

from uis_r_us.widgets import embed_widgets

def dashboard(request, reqpath):
    context = RequestContext(request)
    if not reqpath in ["", "lga", "lga/"]:
        return HttpResponseRedirect("/ui/")
    if reqpath in ["lga", "lga/"]:
        return lga_view(context)
    else:
        return country_view(context)

def country_view(context):
    context.site_title = "Nigeria"
    embed_widgets(context, "country")
    return render_to_response("ui.html", context_instance=context)

def lga_view(context):
    context.site_title = "LGA View"
    embed_widgets(context, "lga")
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