from csv_export import csv_export
from xls_export import xls_export
from single_survey_submission import survey_responses, survey_media_files

# map view
from django.shortcuts import render_to_response
from django.template import RequestContext
import json
from odk_viewer.models import ParsedInstance


def average(values):
    return sum(values, 0.0) / len(values)


def map(request, id_string):
    context = RequestContext(request)
    points = ParsedInstance.objects.values('lat', 'lng', 'instance').filter(instance__user=request.user, instance__xform__id_string=id_string)
    center = {
        'lat': average([p['lat'] for p in points]),
        'lng': average([p['lng'] for p in points]),
        }
    context.points = json.dumps(list(points))
    context.center = json.dumps(center)
    return render_to_response('map.html', context_instance=context)
