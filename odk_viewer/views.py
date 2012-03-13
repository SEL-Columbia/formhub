import json
import os
import urllib2
import zipfile
from tempfile import NamedTemporaryFile
from time import strftime, strptime
from datetime import date
from urlparse import urlparse
from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.files.storage import get_storage_class
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseForbidden,\
         HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

from odk_logger.models import XForm, Instance
from odk_logger.xform_instance_parser import xform_instance_to_dict
from odk_viewer.models import DataDictionary, ParsedInstance
from pyxform import Section, Question
from utils.logger_tools import response_with_mimetype_and_name,\
         disposition_ext_and_date, round_down_geopoint
from utils.viewer_tools import image_urls, image_urls_for_form
from utils.user_auth import has_permission, get_xform_and_perms
from main.models import UserProfile
from csv_writer import CsvWriter
from xls_writer import XlsWriter

def encode(time_str):
    time = strptime(time_str, "%Y_%m_%d_%H_%M_%S")
    return strftime("%Y-%m-%d %H:%M:%S", time)

def dd_for_params(id_string, owner, request):
    start = end = None
    dd = DataDictionary.objects.get(id_string=id_string,
                                    user=owner)
    if request.GET.get('start'):
        try:
            start = encode(request.GET['start'])
        except ValueError:
            # bad format
            return [False,
                HttpReponseBadRequest(
                        'Start time format must be YY_MM_DD_hh_mm_ss')
            ]
        dd.surveys_for_export = lambda d: d.surveys.filter(
                date_created__gte=start)
    if request.GET.get('end'):
        try:
            end = encode(request.GET['end'])
        except ValueError:
            # bad format
            return [False,
                HttpReponseBadRequest(
                        'End time format must be YY_MM_DD_hh_mm_ss')
            ]
        dd.surveys_for_export = lambda d: d.surveys.filter(
                date_created__lte=end)
    if start and end:
        dd.surveys_for_export = lambda d: d.surveys.filter(
                date_created__lte=end, date_created__gte=start)
    return [True, dd]

def parse_label_for_display(pi, xpath):
    label = pi.data_dictionary.get_label(xpath)
    if not type(label) == dict:
        label = { 'Unknown': label }
    return label.items()

def average(values):
    if len(values):
        return sum(values, 0.0) / len(values)
    return None


def map_view(request, username, id_string):
    xform = XForm.objects.get(user__username=username, id_string=id_string)
    owner = User.objects.get(username=username)
    if not has_permission(xform, owner, request):
        return HttpResponseForbidden('Not shared.')
    context = RequestContext(request)
    context.content_user = owner
    context.xform = xform
    context.profile, created = UserProfile.objects.get_or_create(user=owner)
    points = ParsedInstance.objects.values('lat', 'lng', 'instance').filter(
        instance__user=owner,
        instance__xform__id_string=id_string,
        lat__isnull=False,
        lng__isnull=False)
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
    context.form_view = True
    return render_to_response('map.html', context_instance=context)


# TODO: do a good job of displaying hierarchical data
def survey_responses(request, instance_id):
    pi = get_object_or_404(ParsedInstance, instance=instance_id)
    xform, is_owner, can_edit, can_view = get_xform_and_perms(\
            pi.instance.user.username, pi.instance.xform.id_string, request)
    # no access
    if not (xform.shared_data or can_view or
            request.session.get('public_link')):
        return HttpResponseRedirect('/')
    data = pi.to_dict()

    # get rid of keys with leading underscores
    data_for_display = {}
    for k, v in data.items():
        if not k.startswith(u"_"):
            data_for_display[k] = v

    xpaths = data_for_display.keys()
    xpaths.sort(cmp=pi.data_dictionary.get_xpath_cmp())
    label_value_pairs = [
         (parse_label_for_display(pi, xpath),
         data_for_display[xpath]) for xpath in xpaths
    ]
    languages = label_value_pairs[-1][0]
    return render_to_response('survey.html', {
            'label_value_pairs': label_value_pairs,
            'image_urls': image_urls(pi.instance),
            'languages': languages,
            'default_language': languages[0][0]
            })


def csv_export(request, username, id_string):
    owner = User.objects.get(username=username)
    xform = XForm.objects.get(id_string=id_string, user=owner)
    if not has_permission(xform, owner, request):
        return HttpResponseForbidden('Not shared.')
    valid, dd = dd_for_params(id_string, owner, request)
    if not valid: return dd
    writer = CsvWriter(dd, dd.get_data_for_excel(), dd.get_keys(),\
            dd.get_variable_name)
    file_path = writer.get_default_file_path()
    writer.write_to_file(file_path)
    if request.GET.get('raw'):
        id_string = None
    response = response_with_mimetype_and_name('application/csv', id_string,
        extension='csv',
        file_path=file_path, use_local_filesystem=True)
    return response


def xls_export(request, username, id_string):
    owner = User.objects.get(username=username)
    xform = XForm.objects.get(id_string=id_string, user=owner)
    if not has_permission(xform, owner, request):
        return HttpResponseForbidden('Not shared.')
    valid, dd = dd_for_params(id_string, owner, request)
    if not valid: return dd
    ddw = XlsWriter()
    ddw.set_data_dictionary(dd)
    temp_file = ddw.save_workbook_to_file()
    if request.GET.get('raw'):
        id_string = None
    response = response_with_mimetype_and_name('vnd.ms-excel', id_string,
        extension='xls')
    response.write(temp_file.getvalue())
    temp_file.seek(0, os.SEEK_END)
    response['Content-Length'] = temp_file.tell()
    temp_file.close()
    return response


def zip_export(request, username, id_string):
    owner = User.objects.get(username=username)
    xform = XForm.objects.get(id_string=id_string, user=owner)
    if not has_permission(xform, owner, request):
        return HttpResponseForbidden('Not shared.')
    dd = DataDictionary.objects.get(id_string=id_string,
                                    user=owner)
    if request.GET.get('raw'):
        id_string = None
    # create zip_file
    tmp = NamedTemporaryFile()
    z = zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED)
    photos = image_urls_for_form(xform)
    for photo in photos:
        f = NamedTemporaryFile()
        req = urllib2.Request(photo)
        f.write(urllib2.urlopen(req).read())
        f.seek(0)
        z.write(f.name, urlparse(photo).path[1:])
        f.close()
    z.close()
    if request.GET.get('raw'):
        id_string = None
    response = response_with_mimetype_and_name('zip', id_string,
            file_path=tmp.name, use_local_filesystem=True)
    return response


def kml_export(request, username, id_string):
    # read the locations from the database
    context = RequestContext(request)
    context.message="HELLO!!"
    owner = User.objects.get(username=username)
    xform = XForm.objects.get(id_string=id_string, user=owner)
    if not has_permission(xform, owner, request):
        return HttpResponseForbidden('Not shared.')
    dd = DataDictionary.objects.get(id_string=id_string,
                                    user=owner)
    pis = ParsedInstance.objects.filter(instance__user=owner, instance__xform__id_string=id_string, lat__isnull=False, lng__isnull=False)
    data_for_template = []
    for pi in pis:
        # read the survey instances
        data = pi.to_dict()
        # get rid of keys with leading underscores
        data_for_display = {}
        for k, v in data.items():
            if not k.startswith(u"_"):
                data_for_display[k] = v
        xpaths = data_for_display.keys()
        xpaths.sort(cmp=pi.data_dictionary.get_xpath_cmp())
        label_value_pairs = [
            (pi.data_dictionary.get_label(xpath),
            data_for_display[xpath]) for xpath in xpaths]
        table_rows = []
        for key, value in label_value_pairs:
            table_rows.append('<tr><td>%s</td><td>%s</td></tr>' % (key, value))
        img_urls = image_urls(pi.instance)
        img_url = img_urls[0] if img_urls else ""
        data_for_template.append({"name":id_string, "id": pi.id, "lat": pi.lat, "lng": pi.lng,'image_urls': img_urls, "table": '<table border="1"><a href="#"><img width="210" class="thumbnail" src="%s" alt=""></a><%s</table>' % (img_url,''.join(table_rows))})
    context.data = data_for_template
    response = render_to_response("survey.kml",
        context_instance=context,
        mimetype="application/vnd.google-earth.kml+xml")
    response['Content-Disposition'] = disposition_ext_and_date(id_string, 'kml')
    return response
