from collections import defaultdict
# map view
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.shortcuts import render_to_response
# http://djangosnippets.org/snippets/365/
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseNotAllowed
from odk_logger.models import XForm, Instance
from odk_viewer.models import DataDictionary, ParsedInstance
from odk_logger.utils import round_down_geopoint
from odk_logger.xform_instance_parser import xform_instance_to_dict
from pyxform import Section, Question
from odk_logger.utils import response_with_mimetype_and_name,\
     disposition_ext_and_date
from django.contrib.auth.models import User
from main.models import UserProfile

from csv_writer import CsvWriter
from csv_writer import DataDictionaryWriter
from xls_writer import XlsWriter
from xls_writer import DataDictionary

import json
import os
from datetime import date

def parse_label_for_display(pi, xpath):
    label = pi.data_dictionary.get_label(xpath)
    if type(label) == dict:
        label = ["%s: %s" % (key, value) for key, value in label.items()]
        label = "<br/>".join(label)
    return label

def average(values):
    if len(values):
        return sum(values, 0.0) / len(values)
    return None


def map_view(request, username, id_string):
    xform = XForm.objects.get(user__username=username, id_string=id_string)
    owner = User.objects.get(username=username)
    if not (xform.shared_data or owner == request.user):
        return HttpResponseNotAllowed('Not shared.')
    context = RequestContext(request)
    context.content_user = owner
    context.xform = xform
    context.profile, created = UserProfile.objects.get_or_create(user=owner)
    points = ParsedInstance.objects.values('lat', 'lng', 'instance').filter(instance__user=owner, instance__xform__id_string=id_string, lat__isnull=False, lng__isnull=False)
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
    context.map_view = True
    return render_to_response('map.html', context_instance=context)


def survey_responses(request, pk):
    # todo: do a good job of displaying hierarchical data
    pi = ParsedInstance.objects.get(instance=pk)
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

    return render_to_response('survey.html', {
            'label_value_pairs': label_value_pairs,
            'image_urls': image_urls(pi.instance),
            })


def image_urls(instance):
    return [a.media_file.url for a in instance.attachments.all()]


def csv_export(request, username, id_string):
    owner = User.objects.get(username=username)
    dd = DataDictionary.objects.get(id_string=id_string,
                                    user=owner)
    if not dd.shared_data and request.user.username != username:
        return HttpResponseNotAllowed('Not shared.')
    writer = DataDictionaryWriter(dd)
    file_path = writer.get_default_file_path()
    writer.write_to_file(file_path)
    response = response_with_mimetype_and_name('application/csv', id_string, extension='csv',
            file_path=file_path, use_local_filesystem=True)
    return response


def xls_export(request, username, id_string):
    owner = User.objects.get(username=username)
    dd = DataDictionary.objects.get(id_string=id_string,
                                    user=owner)
    if not dd.shared_data and request.user.username != username:
        return HttpResponseNotAllowed('Not shared.')
    ddw = XlsWriter()
    ddw.set_data_dictionary(dd)
    temp_file = ddw.save_workbook_to_file()
    response = response_with_mimetype_and_name('vnd.ms-excel', id_string, extension='xls')
    response.write(temp_file.getvalue())
    temp_file.close()
    return response


def zip_export(request, username, id_string):
    owner = User.objects.get(username=username)
    dd = DataDictionary.objects.get(id_string=id_string,
                                    user=owner)
    if not dd.shared_data and request.user.username != username:
        return HttpResponseNotAllowed('Not shared.')
    response = response_with_mimetype_and_name('zip', id_string)
    # TODO create that zip_file
    zip_file = None
    response.content = zip_file
    return response


def kml_export(request, username, id_string):
    # read the locations from the database
    context = RequestContext(request)
    context.message="HELLO!!"
    owner = User.objects.get(username=username)
    dd = DataDictionary.objects.get(id_string=id_string,
                                    user=owner)
    if not dd.shared_data and request.user.username != username:
        return HttpResponseNotAllowed('Not shared.')
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

