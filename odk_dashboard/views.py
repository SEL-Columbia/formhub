import re
from django.utils import simplejson
from django.shortcuts import render_to_response
from djangomako import shortcuts
from django.db.models import Avg, Max, Min, Count
from django.http import HttpResponse, HttpResponseRedirect
from odk_dropbox import utils
from odk_dropbox.models import Form
from .models import ParsedInstance, Phone, District
import datetime


def ensure_logged_in(request):
    resp = "OK"
    if request.user.is_authenticated():
        return HttpResponseRedirect("/main/")
    else:
        return HttpResponseRedirect("/accounts/login")

def main_index(request):
    info={}
    info['user'] = request.user
    return render_to_response("index.html", info)

def dashboard(request):
    info = {}
    info['table_types'] = simplejson.dumps(dimensions.keys())
    districts = District.objects.filter(active=True)
    info['districts'] = simplejson.dumps([x.to_dict() for x in districts])
    forms = Form.objects.all()
    info['surveys'] = simplejson.dumps(list(set([x.title for x in forms])))
    info['user'] = request.user
#    return HttpResponse(request.user)
    return render_to_response('dashboard.html', info)

def recent_activity(request):
    info={}
    info['submissions'] = ParsedInstance.objects.all().order_by('-end')[0:50]
    return render_to_response("activity.html", info)

dimensions = {
    "survey" : "survey_type__name",
    "surveyor" : "phone__most_recent_surveyor__first_name",
    "date" : "date",
    "location" : "location__name",
    }

def frequency_table_urls(request):
    info = {"urls" : []}
    keys = dimensions.keys()
    for i in range(0,len(keys)):
        for j in range(i+1,len(keys)):
            info["urls"].append(
                "submission-counts/%(row)s/%(column)s" % {
                    "row" : keys[i],
                    "column" : keys[j]
                    }
                )
    print info
    return render_to_response("url_list.html", info)

def frequency_table(request, rows, columns):
    r = dimensions[rows]
    c = dimensions[columns]

    dicts = ParsedInstance.objects.values(r, c).annotate(count=Count("id"))
    info = {"cells" : dict( [((d[r], d[c]), d["count"]) for d in dicts] )}
        
    row_headers = []
    column_headers = []
    for d in dicts:
        if d[r] not in row_headers: row_headers.append(d[r])
        if d[c] not in column_headers: column_headers.append(d[c])

    row_headers.sort()
    column_headers.sort()

    info["row_headers"] = row_headers
    info["column_headers"] = column_headers

    return shortcuts.render_to_response("table.html", info)

def profiles_section(request):
    info = {'sectionname':'profiles'}
    return render_to_response("profiles.html", info)

def data_section(request):
    info = {'sectionname':'data'}
    return render_to_response("data.html", info)

def view_section(request):
    info = {'sectionname':'view'}
    pass_to_map = {'all':[],'surveyors':[], \
        'survey':[],'recent':[]}
    
    psubs = []
    for ps in ParsedInstance.objects.exclude(location__gps=None):
        pcur = {}
        if ps.location.gps:
            pcur['images'] = [x.image.url for x in ps.instance.images.all()]
            pcur['phone'] = ps.phone.__unicode__()
            pcur['date'] = ps.end.strftime("%Y-%m-%d %H:%M")
            pcur['survey_type'] = ps.survey_type.name
            pcur['gps'] = ps.location.gps.to_dict()
            pcur['title'] = ps.survey_type.name
        psubs.append(pcur)
    
    pass_to_map['all'] = psubs
    info['point_data'] = simplejson.dumps(pass_to_map)
    return render_to_response("view.html", info)

def survey_times(request):
    """
    Get the average time spent on each survey type. It looks like we
    need to add a field to ParsedInstance model to keep track of end
    minus start times.
    """
    times = {}
    for ps in ParsedInstance.objects.all():
        name = ps.survey_type.name
        if name not in times:
            times[name] = []
        times[name].append(ps.end - ps.start)
    for k, v in times.items():
        v.sort()
        times[k] = v[len(v)/2]
    return render_to_response("dict.html", {"dict":times})

def date_tuple(t):
    return (t.year, t.month, t.day)

def average(l):
    result = datetime.timedelta(0)
    for x in l:
        result = result + x/len(l)
    return result

def remove_saved_later(l):
    for i in range(len(l)-1):
        # end of this one > start of next one
        if l[i][1] > l[i+1][0]:
            return l.pop(i)
    return None

def median_time_between_surveys(request):
    """
    Get the average time spent between surveys.
    """
    times = {}
    for ps in ParsedInstance.objects.all():
        date = date_tuple(ps.start)
        if date==date_tuple(ps.end):
            k = (ps.phone.device_id, date[0], date[1], date[2])
            if k not in times: times[k] = []
            times[k].append((ps.start, ps.end))
    for k, v in times.items():
        v.sort()
        saved_later = remove_saved_later(v)
        while saved_later:
            saved_later = remove_saved_later(v)
    diffs = []
    for k, v in times.items():
        v.sort()
        if len(v)>1:
            diffs.extend( [v[i+1][0] - v[i][1] for i in range(len(v)-1)] )
    diffs.sort()
    d = {"median time between surveys" : diffs[len(diffs)/2],
         "average time between surveys" : average(diffs)}
    return render_to_response("dict.html", {"dict" : d})

def analysis_section(request):
    info = {'sectionname':'analysis'}
    return render_to_response("analysis.html", info)

def embed_survey_instance_data(request, survey_id):
    ps = ParsedInstance.objects.get(pk=survey_id)
    d = utils.parse_instance(ps.instance).get_dict()
    keys = ["community", "ward", "name"]
    info = {'survey_id':survey_id,
            'data': [(k.title(), d[k].title()) for k in keys]}
    return render_to_response("survey_instance_data.html", info)
