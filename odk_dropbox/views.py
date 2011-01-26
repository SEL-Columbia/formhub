#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseBadRequest

import itertools
import xlwt
import json
from bson import json_util
from . import utils, tag
from .models import District, XForm, get_or_create_instance, xform_instances

@require_GET
def formList(request):
    """This is where ODK Collect gets its download list."""
    forms = [f.id_string for f in XForm.objects.filter(active=True)]
    return render_to_response("formList.xml",
                              {"forms": forms},
                              mimetype="application/xml")

@require_POST
@csrf_exempt
def submission(request):
    # request.FILES is a django.utils.datastructures.MultiValueDict
    # for each key we have a list of values
    try:
        xml_file_list = request.FILES.pop("xml_submission_file", [])

        # save this XML file and media files as attachments
        instance, created = get_or_create_instance(
            xml_file_list[0],
            list(itertools.chain(*request.FILES.values()))
            )

        # ODK needs two things for a form to be considered successful
        # 1) the status code needs to be 201 (created)
        # 2) The location header needs to be set to the host it posted to
        response = HttpResponse("Your ODK submission was successful.")
        response.status_code = 201
        response['Location'] = "http://%s/submission" % request.get_host()
        return response
    except:
        # catch any exceptions and print them to the error log
        # it'd be good to add more info to these error logs
        return HttpResponseBadRequest(
            "We need to improve our error messages and logging."
            )

read_all_data, created = Permission.objects.get_or_create(
    name = "Can read all data",
    content_type = ContentType.objects.get_for_model(Permission),
    codename = "read_all_data"
    )
@permission_required("auth.read_all_data")
def export_list(request):
    return HttpResponse("<blink>Survey List Goes Here</blink>")
    return render_to_response(
        "export_list.html",
        {"xforms" : XForm.objects.filter(active=True)}
        )

def dashboard(request):
    info = {}
#    info['table_types'] = simplejson.dumps(dimensions.keys())
    info['table_types'] = json.dumps(['a','b','c'])
    info['districts'] = json.dumps([x.to_dict() for x in District.objects.filter(active=True)])
    forms = XForm.objects.all()
    info['surveys'] = json.dumps(list(set([x.title for x in forms])))
    info['user'] = request.user
    return render_to_response("dashboard.html", info)

def map_data_points(request):
    dict_list = list(xform_instances.find(
        spec={tag.GPS : {"$exists" : True}},
#        fields=[tag.GPS, tag.DOC_NAME, tag.DISTRICT_ID]
        ))
    
    map_pt_list = []
    for mp in dict_list:
        val = {}
        geopoint = mp[u'geopoint']
        val = {'id': mp['_id'], 'district_id': mp['_district_id'], \
                'survey_type': mp['_survey_type'], 'picture': mp['picture']}
        
    #image_url is composed by combining "/site_media/instances/{form_id}/{picture}"
        val['form_id'] = mp['_form_id']
        
    #need to get cleaned values for these:
        val['surveyor'] = 'bob'
        val['phone'] = "911"
        val['title'] = "Instance ID: %s" % val['id']
        val['datetime'] = '2010-12-21 09:34'
#        from ipdb import set_trace as debug; debug() 
        if geopoint is not None:
            val['gps'] = {'lat':geopoint[u'latitude'], 'lng':geopoint[u'longitude']}
        map_pt_list.append(val)
    return HttpResponse(json.dumps(map_pt_list, default=json_util.default))

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
    for i in xform.instances():
        row = []
        for h in headers:
            row.append(d.get(h, u"n/a"))
        table.append(row)

    wb = xlwt.Workbook()
    ws = wb.add_sheet("Data")
    for r in range(len(table)):
        for c in range(len(table[r])):
            ws.write(r, c, table[r][c])

    return xls_to_response(wb, form.id_string + ".xls")

# import re
# from django.utils import simplejson
# from django.shortcuts import render_to_response
# from djangomako import shortcuts
# from django.db.models import Avg, Max, Min, Count
# from django.http import HttpResponse, HttpResponseRedirect
# from odk_dropbox import utils
# from odk_dropbox.models import Form
# from odk_dropbox.models import Form, odk_db
# from .models import ParsedInstance, Phone, District
# import datetime


# def ensure_logged_in(request):
#     resp = "OK"
#     if request.user.is_authenticated():
#         return HttpResponseRedirect("/main/")
#     else:
#         return HttpResponseRedirect("/accounts/login")

# def main_index(request):
#     info={}
#     info['user'] = request.user
#     return render_to_response("index.html", info)

# def dashboard(request):
#     info = {}
#     info['table_types'] = simplejson.dumps(dimensions.keys())
#     districts = District.objects.filter(active=True)
#     info['districts'] = simplejson.dumps([x.to_dict() for x in districts])
#     forms = Form.objects.all()
#     info['surveys'] = simplejson.dumps(list(set([x.title for x in forms])))
#     info['user'] = request.user
# #    return HttpResponse(request.user)
#     return render_to_response('dashboard.html', info)

# def recent_activity(request):
#     info={}
#     info['submissions'] = ParsedInstance.objects.all().order_by('-end')[0:50]
#     return render_to_response("activity.html", info)

# dimensions = {
#     "survey" : "survey_type__name",
#     "surveyor" : "phone__most_recent_surveyor__first_name",
#     "date" : "date",
#     "location" : "location__name",
#     }

# def frequency_table_urls(request):
#     info = {"urls" : []}
#     keys = dimensions.keys()
#     for i in range(0,len(keys)):
#         for j in range(i+1,len(keys)):
#             info["urls"].append(
#                 "submission-counts/%(row)s/%(column)s" % {
#                     "row" : keys[i],
#                     "column" : keys[j]
#                     }
#                 )
#     return render_to_response("url_list.html", info)

# def frequency_table(request, rows, columns):
#     r = dimensions[rows]
#     c = dimensions[columns]

#     dicts = ParsedInstance.objects.values(r, c).annotate(count=Count("id"))
#     info = {"cells" : dict( [((d[r], d[c]), d["count"]) for d in dicts] )}
        
#     row_headers = []
#     column_headers = []
#     for d in dicts:
#         if d[r] not in row_headers: row_headers.append(d[r])
#         if d[c] not in column_headers: column_headers.append(d[c])

#     row_headers.sort()
#     column_headers.sort()

#     info["row_headers"] = row_headers
#     info["column_headers"] = column_headers

#     return shortcuts.render_to_response("table.html", info)

# def profiles_section(request):
#     info = {'sectionname':'profiles'}
#     return render_to_response("profiles.html", info)

# def data_section(request):
#     info = {'sectionname':'data'}
#     return render_to_response("data.html", info)

# def view_section(request):
#     info = {'sectionname':'view'}
#     pass_to_map = {'all':[],'surveyors':[], \
#         'survey':[],'recent':[]}
    
#     psubs = []
#     for ps in ParsedInstance.objects.exclude(location__gps=None):
#         pcur = {}
#         if ps.location.gps:
#             pcur['images'] = [x.image.url for x in ps.instance.images.all()]
#             pcur['phone'] = ps.phone.__unicode__()
#             pcur['date'] = ps.end.strftime("%Y-%m-%d %H:%M")
#             pcur['survey_type'] = ps.survey_type.name
#             pcur['gps'] = ps.location.gps.to_dict()
#             pcur['title'] = ps.survey_type.name
#         psubs.append(pcur)
    
#     pass_to_map['all'] = psubs
#     info['point_data'] = simplejson.dumps(pass_to_map)
#     return render_to_response("view.html", info)

# def couchly(request, survey_id):
#     info = {}
#     if survey_id != '':
#         info['survey_id'] = survey_id
#         info['display_dictionary'] = {'teachers_and_staff':'Teachers and Staff', \
#             'geopoint':'GPS Coordinates', 'name': 'Name', 'community': 'Community', \
#             'survey_data':'Survey Data'}
#         info['survey_data'] = simplejson.dumps(odk_db.get(survey_id)['parsed_xml'])
#     else:
#         info['survey_list'] = [{'name':'Education 1', 'id':'#'}, \
#                 {'name':'Health 1', 'id': '#'}, \
#                 {'name':'Water 1', 'id': '#'}]
    
#     return render_to_response("couchly.html", info)

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

# def date_tuple(t):
#     return (t.year, t.month, t.day)

# def average(l):
#     result = datetime.timedelta(0)
#     for x in l:
#         result = result + x/len(l)
#     return result

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

# def analysis_section(request):
#     info = {'sectionname':'analysis'}
#     return render_to_response("analysis.html", info)

# def embed_survey_instance_data(request, survey_id):
#     ps = ParsedInstance.objects.get(pk=survey_id)
#     d = utils.parse_instance(ps.instance).get_dict()
#     keys = ["community", "ward", "name"]
#     info = {'survey_id':survey_id,
#             'data': [(k.title(), d.get(k,"").title()) for k in keys]}
#     return render_to_response("survey_instance_data.html", info)
