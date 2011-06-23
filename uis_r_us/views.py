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

def variable_data(request):
    variable_data = {
        "sectors": [
            {
              "name": "Health",
              "slug": "health",
              "columns": [
                {"slug": "facility_name", "name": "Name"},
                {"slug": "facility_type", "name": "Type"},
                {"slug": "power_sources_none", "name": "No Power Source"},
                {"slug": "facility_owner_manager", "name": "Owner/Manager"},
                {"slug": "all_weather_road_yn", "name": "All-weather Road"},
                {"slug": "health_facility_condition", "name": "Condition"}
              ]
            }
        ]
    }
    import json
    return HttpResponse(json.dumps(variable_data))