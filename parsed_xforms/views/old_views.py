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
from django.template import RequestContext

import itertools
import json
import re

from parsed_xforms.models import xform_instances, ParsedInstance
from common_tags import *
from xform_manager.models import XForm, Instance
from nga_districts.models import LGA, Zone, State
from deny_if_unauthorized import deny_if_unauthorized

from parsed_xforms.view_pkgr import ViewPkgr

@deny_if_unauthorized()
def export_list(request):
    xforms = XForm.objects.all()
    context = RequestContext(request, {"xforms" : xforms})
    return render_to_response(
        "export_list.html",
        context_instance=context
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

@deny_if_unauthorized()
def submission_counts_by_lga(request, as_dict=False):
    dicts = ParsedInstance.objects.values(
        "lga", "instance__xform__title"
        ).annotate(count=Count("id"))

    titles = [u"Agriculture", u"Education", u"Health", u"LGA", u"Water"]
    headers = [u"Zone", u"State", u"LGA"] + titles

    lgas = LGA.get_ordered_phase2_query_set()
    rows = []
    for lga in lgas:
        row = [lga.state.zone.name,
               lga.state.name,
               lga.name,]
        for title in titles:
            count = ParsedInstance.objects.filter(
                lga=lga, instance__xform__title=title
                ).count()
            row.append(count)
        rows.append(row)
    
    if as_dict: return {"headers" : headers, "rows" : rows}
    
    context = RequestContext(request, {"headers" : headers, "rows" : rows})
    return render_to_response(
        "submission_counts_by_lga.html",
        context_instance=context
        )

from map_xforms.models import SurveyTypeMapData

from django.forms.models import model_to_dict

from collections import defaultdict

@deny_if_unauthorized()
def dashboard(request):
    rc = RequestContext(request)
    rc.xforms = XForm.objects.all()
    rc.lga_table = submission_counts_by_lga(request, True)
    rc.table_types = json.dumps(dimensions.keys())
    rc.survey_types = [model_to_dict(s) for s in SurveyType.objects.all()]
    
    rc.zone_table = state_count_dict()
    
    return render_to_response(
        "dashboard.html",
        context_instance=rc
        )

def state_count_dict():
    """
    This is similar to submission_counts_by_lga except the data is ordered by Zone, State, then LGA
    """
    lga_query = LGA.get_ordered_phase2_query_set()

    row_groups = []
    titles = [u"Agriculture", u"Education", u"Health", u"LGA", u"Water"]
    
    survey_totals = defaultdict(int)
    lgas_by_state = defaultdict(list)
    zone_totals = {}
    state_totals = {}
    lga_totals = {}
    total_total = 0
    
    states_list = []
    
    for lga in lga_query.all():
        totals_for_this_lga = {}
        cur_state = lga.state
        cur_zone = cur_state.zone
        if cur_state not in states_list: states_list.append(cur_state)
        if cur_state not in state_totals: state_totals[cur_state] = defaultdict(int)
        if cur_zone not in zone_totals: zone_totals[cur_zone] = defaultdict(int)
        
        #this is one way to keep lga list so we can package it up later.
        lgas_by_state[cur_state].append(lga)
        
        lga_total = 0
        for title in titles:
            count = ParsedInstance.objects.filter(
                        lga=lga, instance__xform__title=title
                    ).count()
            state_totals[cur_state][title] += count
            zone_totals[cur_zone][title] += count
            survey_totals[title] += count
            lga_total += count
            total_total += count
            totals_for_this_lga[title] = count
        
        totals_for_this_lga['total'] = lga_total
        lga_totals[lga] = totals_for_this_lga
    
    survey_totals_by_title = []
    for title in titles:
        survey_totals_by_title.append(survey_totals[title])
    
    for state in states_list:
        totals_by_title = []
        state_total = 0
        for title in titles:
            val = state_totals[state][title]
            totals_by_title.append(val)
            state_total += val
        lga_list = []
        for lga in lgas_by_state[state]:
            cur_lga_total = lga_totals[lga]
            lga_totals_by_title = []
            for title in titles:
                lga_totals_by_title.append(cur_lga_total[title])
            lga_list.append({'name':lga.name, 'total_count':cur_lga_total['total'], \
                            'pk': lga.id, 'survey_totals_by_title': lga_totals_by_title})
        
        row_groups.append({'zone_name': state.zone.name, 'name': state.name, \
                    'survey_totals_by_title': totals_by_title, 'total_count': state_total, \
                    'lga_count': len(lga_list), 'lga_list': lga_list})
    
    return {
        'survey_titles': titles,
        'survey_totals_by_title': survey_totals_by_title,
        'states': row_groups,
        'total_total': total_total
    }


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
    d['submissions'] = Instance.objects.filter(survey_type__id=st.id).count()
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
