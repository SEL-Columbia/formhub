#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.db.models import Avg, Max, Min, Count

import itertools
import xlwt
import json
import re
from bson import json_util
from . import utils, tag
from parsed_xforms.models import xform_instances, ParsedInstance
from xform_manager.models import XForm, Instance
from locations.models import District

from view_pkgr import ViewPkgr

read_all_data, created = Permission.objects.get_or_create(
    name = "Can read all data",
    content_type = ContentType.objects.get_for_model(Permission),
    codename = "read_all_data"
    )
@permission_required("auth.read_all_data")
def export_list(request):
    return render_to_response(
        "export_list.html",
        {"xforms" : XForm.objects.all()}
        )

def prep_info(request):
    """
    This function is meant to be reused and provide the user object. If no user object, then
    provide the login form.
    
    We might decide that this function is a lame attempt to have global variables passed
    to django templates, and should be deleted.
    """
    info = {'user':request.user}
    return info
        
def map_data_points(request):
    """
    The map list needs these attributes for each survey to display
    the map & dropdown filters.
    
    * Submission/Instance/Mongo doc ID
    * Date
    * Surveyor name
    * Survey Type
    * District ID
    * a URL to access the picture
    * GPS coordinates
    
    """
    dict_list = list(xform_instances.find(
            spec={tag.GPS : {"$exists" : True}},
            fields=[tag.DATE_TIME_START, tag.SURVEYOR_NAME, tag.INSTANCE_DOC_NAME, tag.DISTRICT_ID, tag.GPS]
            ))
    
    return HttpResponse(json.dumps(dict_list, default=json_util.default))

def xls_to_response(xls, fname):
    response = HttpResponse(mimetype="application/ms-excel")
    response['Content-Disposition'] = 'attachment; filename=%s' % fname
    xls.save(response)
    return response

@permission_required("auth.read_all_data")
def xls(request, id_string):
    xform = XForm.objects.get(id_string=id_string)
    xform.guarantee_parser()
    headers = []
    for path, attributes in xform.parser.get_variable_list():
        headers.append(path)
    table = [headers]
    for i in xform.surveys.all():
        row = []
        d = i.get_from_mongo()
        for h in headers:
            row.append(str(d.get(h, u"n/a")))
        table.append(row)

    wb = xlwt.Workbook()
    ws = wb.add_sheet("Data")
    for r in range(len(table)):
        for c in range(len(table[r])):
            ws.write(r, c, table[r][c])

    return xls_to_response(wb, re.sub(r"\s+", "_", id_string) + ".xls")

dimensions = {
    "survey" : "survey_type__slug",
    "surveyor" : "surveyor__name",
    "date" : "date",
    "location" : "district",
    }

def frequency_table(request, rows, columns):
    r = dimensions[rows]
    c = dimensions[columns]

    dicts = Instance.objects.values(r, c).annotate(count=Count("id"))
    for d in dicts:
        for k in d.keys():
            d[k] = str(d[k])

    row_headers = []
    column_headers = []
    for d in dicts:
        if d[r] not in row_headers: row_headers.append(d[r])
        if d[c] not in column_headers: column_headers.append(d[c])

    row_headers.sort()
    column_headers.sort()

    cells = {}
    for d in dicts:
        i = row_headers.index(d[r])
        j = column_headers.index(d[c])
        if i in cells: cells[i][j] = d["count"]
        else: cells[i] = {j : d["count"]}

    for i in range(len(row_headers)):
        row_headers[i] = {"id" : i, "text" : row_headers[i]}
    for i in range(len(column_headers)):
        column_headers[i] = {"id" : i, "text" : column_headers[i]}

    table = {
        "row_headers" : row_headers,
        "column_headers" : column_headers,
        "cells" : cells
        }
    return HttpResponse(json.dumps(table, indent=4))

from map_xforms.models import SurveyTypeMapData

def dashboard(request):
    info = prep_info(request)
    info['dashboard_base_url'] = "/xforms/"
    info['table_types'] = json.dumps(dimensions.keys())
    info['districts'] = json.dumps([x.to_dict() for x in District.objects.filter(active=True)])
    forms = XForm.objects.all()
    info['surveys'] = json.dumps(list(set([x.title for x in forms])))
    info['survey_types'] = json.dumps([s.to_dict() for s in SurveyTypeMapData.objects.all()])
    return render_to_response("dashboard.html", info)

from submission_qr.forms import ajax_post_form as quality_review_ajax_form
from submission_qr.views import score_partial

import json

def json_safe(val):
    if val.__class__=={}.__class__:
        res = {}
#        [res[k]=json_safe(v) for k,v in val.items()]
        for k, v in val.items():
            res[k] = json_safe(v)
        return res
    else:
        return str(val)

def survey(request, pk):
    r = ViewPkgr(request, "survey.html")
    
    instance = ParsedInstance.objects.get(pk=pk)
    
    # score_partial is the section of the page that lists scores given
    # to the survey.
    # it also contains a form for editing existing submissions or posting
    # a new one. 
    reviewing = score_partial(instance, request.user, True)

    data = []
    mongo_json = instance.get_from_mongo()
    for key, val in mongo_json.items():
        data.append((key, val))
    
    r.info['survey_title'] = "Survey Title"
    
    r.add_info({"instance" : instance, \
        'data': data, \
       'score_partial': reviewing, \
       'popup': False})
    return r.r()

def xforms_directory(request):
    r = ViewPkgr(request, "xforms_directory.html")
    r.footer()
    r.ensure_logged_in()
    return r.r()

def homepage(request):
    r = ViewPkgr(request, "xforms_directory.html")
    r.footer()
    r.ensure_logged_in()
    return r.r()

from surveyor_manager.models import Surveyor

def surveyor_list_dict(surveyor):
    d = {'name':surveyor.name}
    d['profile_url'] = "/xforms/surveyors/%d" % surveyor.id
    #how do we find district?
    d['district'] = "district-name-goes-here"
    d['number_of_submissions'] = ParsedInstance.objects.filter(surveyor__id=surveyor.id).count()
    all_submissions = ParsedInstance.objects.filter(surveyor__id=surveyor.id)
    all_submission_dates = [s.get_from_mongo().get(u'start', None) for s in all_submissions]

    #if there are any dates...
    if all_submission_dates:
        most_recent_date = all_submission_dates[0]
        for i in all_submission_dates:
            if most_recent_date > i: most_recent_date = i
        d['most_recent_submission'] = most_recent_date
    else:
        d['most_recent_submission'] = "No submissions"
    return d
    
STANDARD_DATE_DISPLAY = "%d-%m-%Y"

def surveyor_profile_dict(surveyor):
    d = {'name': surveyor.name}
#    d['district'] = surveyor.surveys.all()[0].district.name
    d['registered_at'] = "?"
    d['number_of_submissions'] = ParsedInstance.objects.filter(surveyor__id=surveyor.id).count()

    #how should we query submissions?
    d['most_recent_submissions'] = []
    all_submissions = ParsedInstance.objects.filter(surveyor__id=surveyor.id)
    all_submission_dates = [s.get_from_mongo().get(u'start', None) for s in all_submissions]
    if all_submission_dates:
        most_recent_date = all_submission_dates[0]
        for i in all_submission_dates:
            if most_recent_date > i: most_recent_date = i
        d['most_recent_submission'] = most_recent_date
    else:
        d['most_recent_submission'] = "No submissions"
    
    sts = []
    for st in SurveyType.objects.all():
        surveyor_st_count = ParsedInstance.objects.filter(surveyor__id=surveyor.id).count() #&& survey_type is st...
        sts.append({'name': st.slug, 'submissions': surveyor_st_count})
    d['survey_type_counts'] = sts
    return d

def surveyors(request, surveyor_id=None):
    r = ViewPkgr(request, "surveyors_list.html")
    r.footer()
    r.navs([("XForms Overview", "/xforms/"), \
            ("Surveyors", "/xforms/surveyors")])
    
    if surveyor_id is not None:
        surveyor = Surveyor.objects.get(id=surveyor_id)
        r.info['surveyor'] = surveyor_profile_dict(surveyor)
        r.template = "surveyor_profile.html"
        r.nav([surveyor.name, "/xforms/surveyors/%d" % surveyor.id])
    else:
        r.info['surveyors'] = [surveyor_list_dict(s) for s in Surveyor.objects.all()]
    return r.r()

from xform_manager.models import SurveyType

def survey_type_list_dict(st):
    d = {'name': st.slug}
    d['profile_url'] = "/xforms/surveys/%s" % st.slug
    d['submissions'] = 9999
    return d
    
def survey_type_display_dict(st):
    d = {'name': st.slug}
    try:
        map_data = SurveyTypeMapData.objects.get(survey_type=st)
        d['color'] = map_data.color
    except:
        d['color'] = "Black"
    d['number_of_submissions'] = "99945"
    d['number_of_surveyors'] = "39453456"
    return d

def survey_types(request, survey_type_slug=None):
    r = ViewPkgr(request, "survey_type_list.html")
    r.navs([("XForms Overview", "/xforms/"), \
            ("Survey Types", "/xforms/surveys")])
    r.footer()
    if survey_type_slug is not None:
        try:
            survey_type = SurveyType.objects.get(slug=survey_type_slug)
            map_data = SurveyTypeMapData.objects.get(survey_type=survey_type)
            r.info['template_st'] = survey_type_display_dict(survey_type)
            r.template = "survey_type_dashboard.html"
            r.nav((survey_type_slug, "/xforms/surveys/%s" % survey_type_slug))
        except:
            r.redirect_to = "/xforms/surveys"
    else:
        r.info['survey_types'] = [survey_type_list_dict(s) for s in SurveyType.objects.all()]
    return r.r()


# def survey_times(request):
#     """
#     Get the average time spent on each survey type. It looks like we
#     need to add a field to ParsedInstance model to keep track of end
#     minus start times.
#     """
#     times = {}
#     count = {}
#     for ps in ParsedInstance.objects.all():
#         name = ps.survey_type.name
#         if name not in times:
#             times[name] = []
#             count[name] = 0
#         if ps.end.date()==ps.start.date():
#             times[name].append(ps.end - ps.start)
#         else:
#             count[name] += 1
#     for k, v in times.items():
#         v.sort()
#         if v: times[k] = v[len(v)/2]
#         else: del times[k]
#     return render_to_response("dict.html", {"dict":times})

# def remove_saved_later(l):
#     for i in range(len(l)-1):
#         # end of this one > start of next one
#         if l[i][1] > l[i+1][0]:
#             return l.pop(i)
#     return None

# def median_time_between_surveys(request):
#     """
#     Get the average time spent between surveys.
#     """
#     times = {}
#     for ps in ParsedInstance.objects.all():
#         date = date_tuple(ps.start)
#         if date==date_tuple(ps.end):
#             k = (ps.phone.device_id, date[0], date[1], date[2])
#             if k not in times: times[k] = []
#             times[k].append((ps.start, ps.end))
#     for k, v in times.items():
#         v.sort()
#         saved_later = remove_saved_later(v)
#         while saved_later:
#             saved_later = remove_saved_later(v)
#     diffs = []
#     for k, v in times.items():
#         v.sort()
#         if len(v)>1:
#             diffs.extend( [v[i+1][0] - v[i][1] for i in range(len(v)-1)] )
#     diffs.sort()
#     d = {"median time between surveys" : diffs[len(diffs)/2],
#          "average time between surveys" : average(diffs)}
#     return render_to_response("dict.html", {"dict" : d})

# def embed_survey_instance_data(request, survey_id):
#     ps = ParsedInstance.objects.get(pk=survey_id)
#     d = utils.parse_instance(ps.instance).get_dict()
#     keys = ["community", "ward", "name"]
#     info = {'survey_id':survey_id,
#             'data': [(k.title(), d.get(k,"").title()) for k in keys]}
#     return render_to_response("survey_instance_data.html", info)
