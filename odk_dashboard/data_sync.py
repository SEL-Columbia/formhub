import re
from django.utils import simplejson
from django.shortcuts import render_to_response
from djangomako import shortcuts
from django.db.models import Avg, Max, Min, Count
from django.http import HttpResponse
from odk_dropbox import utils
from odk_dropbox.models import Form
from .models import ParsedInstance, Phone
import datetime

def map_data(request, stamp):
    """
    Returns JSON with a stamp to ensure most recent data is sent.
    """
    psubs = []
    pis = ParsedInstance.objects.exclude(location__gps=None)
    for ps in pis:
        pcur = {}
        if ps.location.gps:
            pcur['images'] = [x.image.url for x in ps.instance.images.all()]
            pcur['phone'] = ps.phone.__unicode__()
            pcur['date'] = ps.end.strftime("%Y-%m-%d %H:%M")
            pcur['survey_type'] = ps.survey_type.name
            pcur['gps'] = ps.location.gps.to_dict()
            pcur['title'] = ps.survey_type.name
        psubs.append(pcur)
    return stamped_json_output("count:%s" % len(psubs), psubs, True)

def stamped_json_output(id_stamp, data, flush):
    return HttpResponse(simplejson.dumps({'stamp':id_stamp, \
                        'data':data, 'flush':flush }))