import re
from django.utils import simplejson
from django.shortcuts import render_to_response
from django.db.models import Avg, Max, Min, Count
from django.http import HttpResponse
from odk_dropbox import utils
from odk_dropbox.models import Form
from .models import ParsedSubmission, Phone
import datetime

def dashboard(request):
    return render_to_response('dashboard.html')

def csv_list():
    list = []
    for f in Form.objects.filter(active=True):
        m = re.search(r"^([a-zA-Z]+)", f.id_string)
        name = m.group(1)
        if name!="Bug": list.append(name)
    list.sort()
    return list

def submission_counts(request):
    counts = ParsedSubmission.objects.values("survey_type__name", "phone__device_id").annotate(count=Count("survey_type"))
    table = {}
    rows = []
    cols = []
    for d in counts:
        device_id = d["phone__device_id"]
        phone = Phone.objects.get(device_id=device_id)
        survey = d["survey_type__name"]
        if survey!="bug":
            if device_id not in table:
                table[device_id] = {}
            if survey not in table[device_id]:
                table[device_id][survey] = {}
            table[device_id][survey] = d["count"]
            name = ""
            if phone.most_recent_surveyor:
                name = phone.most_recent_surveyor.name()
            if (device_id, name) not in rows:
                rows.append((device_id, name))
            if survey not in cols:
                cols.append(survey)
    rows.sort()
    cols.sort()
    t = []
    for row in rows:
        t.append([row[0] if not row[1] else row[1]] + [str(table[row[0]].get(col, 0)) for col in cols])
    return render_to_response("submission_counts.html",
                              {"submission_counts" : t,
                               'columns': cols,
                               'sectionname':'data',
                               'csvs' : csv_list()})

def counts_by_date(request):
    # http://stackoverflow.com/questions/722325/django-group-by-strftime-date-format
    select_data = {"date": "strftime('%%Y/%%m/%%d', end)"}
    counts = ParsedSubmission.objects.extra(select=select_data).values("date", "survey_type__name").annotate(count=Count("survey_type")).order_by()

    table = {}
    rows = []
    cols = []
    for d in counts:
        date = d["date"]
        survey = d["survey_type__name"]
        if survey!="bug":
            if date not in table:
                table[date] = {}
            if survey not in table[date]:
                table[date][survey] = {}
            table[date][survey] = d["count"]
            if date not in rows:
                rows.append(date)
            if survey not in cols:
                cols.append(survey)
    rows.sort()
    cols.sort()
    t = []
    for row in rows:
        t.append([row] + [str(table[row].get(col, 0)) for col in cols])
    return render_to_response("submission_counts.html",
                              {"submission_counts" : t,
                               'columns': cols,
                               'sectionname':'data',
                               'csvs' : csv_list()})

def csv(request, name):
    form = Form.objects.get(id_string__startswith=name.title(), active=True)
    handlers = [utils.parse_submission(s) for s in form.submissions.all()]
    dicts = [h.get_dict() for h in handlers]
    table = utils.table(dicts)
    return HttpResponse(utils.csv(table), mimetype="application/csv")

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
    for ps in ParsedSubmission.objects.exclude(gps=None):
        pcur = {}
        if ps.gps:
            pcur['images'] = [x.image.url for x in ps.submission.images.all()]
            pcur['phone'] = ps.phone.__unicode__()
            pcur['date'] = ps.submission.posted.strftime("%Y-%m-%d %H:%M")
            pcur['survey_type'] = ps.survey_type.name
            pcur['gps'] = ps.gps.to_dict()
            pcur['title'] = ps.survey_type.name
        psubs.append(pcur)
    
    pass_to_map['all'] = psubs
    info['point_data'] = simplejson.dumps(pass_to_map)
    return render_to_response("view.html", info)

def survey_times(request):
    """
    Get the average time spent on each survey type. It looks like we
    need to add a field to ParsedSubmission model to keep track of end
    minus start times.
    """
    times = {}
    for ps in ParsedSubmission.objects.all():
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
    for ps in ParsedSubmission.objects.all():
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
