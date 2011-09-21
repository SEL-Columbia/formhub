# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.db.models import Count
from django.template import RequestContext

import json

from odk_viewer.models import ParsedInstance
from common_tags import *
from odk_logger.models import XForm, Instance

#from odk_viewer.view_pkgr import ViewPkgr

def export_list(request):
    xforms = XForm.objects.all()
    context = RequestContext(request, {"xforms": xforms})
    return render_to_response(
        "export_list.html",
        context_instance=context
        )


def prep_info(request):
    """
    This function is meant to be reused and provide the user
    object. If no user object, then provide the login form.

    We might decide that this function is a lame attempt to have
    global variables passed to django templates, and should be
    deleted.
    """
    info = {'user': request.user}
    return info


dimensions = {
    "survey": "survey_type__slug",
    "date": "date",
    "location": "district",
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
        if d[r] not in row_headers:
            row_headers.append(d[r])
        if d[c] not in column_headers:
            column_headers.append(d[c])

    row_headers.sort()
    column_headers.sort()

    cells = {}
    for d in dicts:
        i = row_headers.index(d[r])
        j = column_headers.index(d[c])
        if i in cells:
            cells[i][j] = d["count"]
        else:
            cells[i] = {j: d["count"]}

    for i in range(len(row_headers)):
        row_headers[i] = {"id": i, "text": row_headers[i]}
    for i in range(len(column_headers)):
        column_headers[i] = {"id": i, "text": column_headers[i]}

    table = {
        "row_headers": row_headers,
        "column_headers": column_headers,
        "cells": cells
        }
    return HttpResponse(json.dumps(table, indent=4))


from django.forms.models import model_to_dict

from collections import defaultdict
from django.conf import settings

def survey(request, pk):
    context = RequestContext(request)
    return render_to_response("survey.html",
        context_instance=context)

STANDARD_DATE_DISPLAY = "%d-%m-%Y"

from odk_logger.models import SurveyType

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
