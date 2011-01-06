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

def activity_list(request, stamp):
    if stamp_up_to_date(ParsedInstance, stamp):
        return HttpResponse(simplejson.dumps("OK"))
    else:
        try:
            stamp_data = simplejson.loads(stamp)
            latest = stamp_data['latest']
            instance_list = ParsedInstance.objects.exclude(location__gps=None).filter(id__gte=latest)
            flush = False
        except:
            instance_list = ParsedInstance.objects.exclude(location__gps=None)
            flush = True

        return stamped_json_output(stamp=model_stamp(ParsedInstance), \
                data=[pi.to_dict() for pi in instance_list], \
                flush=flush)

def stamp_up_to_date(model, stamp):
    return model_stamp(model)==stamp

def model_stamp(model):
    latest_id = model.objects.order_by('-id')[0].id
    count = model.objects.count()
    return "{'count':%s,'latest':%s}" % (count, latest_id)

def stamped_json_output(stamp, data, flush):
    return HttpResponse(simplejson.dumps({'stamp':stamp, \
                        'data':data, 'flush':flush }))
