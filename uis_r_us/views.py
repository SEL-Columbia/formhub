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
              "slug": "water",
              "columns": [
                {"slug": "water_source_type", "name": "Type"},
                {"slug": "lift", "name": "Lift"},
                {"slug": "water_source_developed_by", "name": "Developed by"},
                {"slug": "water_source_used_today_yn", "name": "Used today"},
                {"slug": "water_source_physical_state", "name": "Physical State"}
              ],
              "name": "Water"
            },
            {
              "slug": "education",
              "columns": [
                {"slug": "school_name", "name": "Name"},
                {"slug": "power_sources_none", "name": "No Power Source"},
                {"slug": "water_sources_none", "name": "No Water Source"},
                {"slug": "student_teacher_ratio", "name": "Student/Teacher Ratio"},
                {"slug": "student_teacher_ratio_ok", "name": "Student/Teacher Ratio OK"},
                {"slug": "ideal_number_of_classrooms", "name": "Ideal # of Classrooms"},
                {"slug": "total_number_of_classrooms", "name": "Total # of Classrooms"},
                {"slug": "sufficient_number_of_classrooms", "name": "Sufficient # of Classrooms"},
                {"slug": "percentage_of_classrooms_in_good_condition", "name": "% of Classrooms in Good Condition"}
              ],
              "name": "Education"
            },
            {
              "slug": "health",
              "columns": [
                {"slug": "facility_name", "name": "Name"},
                {"slug": "facility_type", "name": "Type"},
                {"slug": "power_sources_none", "name": "No Power Source",
        		  "description": "Powuer sourlskdjfsldkf",
        		  "counts": {"yes": 12,"no": 28},
        		  "displayColors": {"yes": "#0f0","no": "#f00"}},
                {"slug": "facility_owner_manager", "name": "Owner/Manager"},
                {"slug": "all_weather_road_yn", "name": "All-weather Road",
        "description": "This is da all weader rode, man."},
                {"slug": "health_facility_condition", "name": "Condition"}
              ],
              "name": "Health"
            }
        ]
    }
    import json
    return HttpResponse(json.dumps(variable_data))