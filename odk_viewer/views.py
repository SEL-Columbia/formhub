from collections import defaultdict
# map view
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.shortcuts import render_to_response
# http://djangosnippets.org/snippets/365/
from django.core.servers.basehttp import FileWrapper
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from odk_logger.models import Instance
from odk_viewer.models import DataDictionary
from odk_viewer.models import ParsedInstance
from odk_logger.utils import round_down_geopoint
from odk_logger.xform_instance_parser import xform_instance_to_dict
from pyxform import Section, Question
from odk_logger.utils import response_with_mimetype_and_name

from csv_writer import CsvWriter
from csv_writer import DataDictionaryWriter
from xls_writer import XlsWriter
from xls_writer import DataDictionary

import json
import os
from datetime import date


def average(values):
    if len(values):
        return sum(values, 0.0) / len(values)
    return None


def map_view(request, username, id_string):
    context = RequestContext(request)
    points = ParsedInstance.objects.values('lat', 'lng', 'instance').filter(instance__user=request.user, instance__xform__id_string=id_string, lat__isnull=False, lng__isnull=False)
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
        (pi.data_dictionary.get_label(xpath),
         data_for_display[xpath]) for xpath in xpaths]

    return render_to_response('survey.html', {
            'label_value_pairs': label_value_pairs,
            'image_urls': image_urls(pi.instance),
            })


def image_urls(instance):
    return [a.media_file.url for a in instance.attachments.all()]


def send_file(path, content_type, name):
    """
    Send a file through Django without loading the whole file into
    memory at once. The FileWrapper will turn the file object into an
    iterator for chunks of 8KB.
    """
    wrapper = FileWrapper(file(path))
    response = HttpResponse(wrapper, content_type=content_type)
    response['Content-Disposition'] = 'attachment; filename=%s_%s_data.csv' % (name, date.today().strftime("%Y_%m_%d"))
    response['Content-Length'] = os.path.getsize(path)
    return response


@login_required
def csv_export(request, username, id_string):
    dd = DataDictionary.objects.get(id_string=id_string,
                                    user=request.user)
    writer = DataDictionaryWriter(dd)
    file_path = writer.get_default_file_path()
    writer.write_to_file(file_path)
    return send_file(file_path, "application/csv", id_string)


def xls_export(request, username, id_string):
    dd = DataDictionary.objects.get(id_string=id_string,
                                    user=request.user)
    ddw = XlsWriter()
    ddw.set_data_dictionary(dd)
    temp_file = ddw.save_workbook_to_file()
    response = response_with_mimetype_and_name('vnd.ms-excel', id_string)
    response.write(temp_file.getvalue())
    temp_file.close()
    return response


def zip_export(request, username, id_string):
    response = response_with_mimetype_and_name('zip', id_string)
    # TODO create that zip_file
    response.content = zip_file
    return response


def kml_export(request, username, id_string):
    # read the locations from the database
    context = RequestContext(request)
    context.message="HELLO!!"
    pis = ParsedInstance.objects.filter(instance__user=request.user, instance__xform__id_string=id_string, lat__isnull=False, lng__isnull=False)
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
    response['Content-Disposition'] = 'attachment; filename=%s.kml' %(id_string)
    return response
