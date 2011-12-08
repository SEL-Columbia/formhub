from csv_export import csv_export
from xls_export import xls_export
from single_survey_submission import survey_responses

# map view
from django.shortcuts import render_to_response
from django.template import RequestContext
import json
from odk_viewer.models import ParsedInstance
from odk_logger.utils import round_down_geopoint

def average(values):
    return sum(values, 0.0) / len(values)


def map(request, id_string):
    context = RequestContext(request)
    points = ParsedInstance.objects.values('lat', 'lng', 'instance').filter(instance__user=request.user, instance__xform__id_string=id_string, lat__isnull=False, lng__isnull=False)
    center = {
        'lat': round_down_geopoint(average([p['lat'] for p in points])),
        'lng': round_down_geopoint(average([p['lng'] for p in points])),
        }
    def round_down_point(p):
        return {
            'lat': round_down_geopoint(p['lat']),
            'lng': round_down_geopoint(p['lng']),
            'instance': p['instance']
        }
    context.points = json.dumps([round_down_point(p) for p in list(points)])
    context.center = json.dumps(center)
    return render_to_response('map.html', context_instance=context)
