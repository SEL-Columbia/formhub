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

#from utils.reinhardt import json_response
from csv_writer import CsvWriter
from csv_writer import DataDictionaryWriter
from xls_writer import XlsWriter
from xls_writer import DataDictionary

import json
import os

def average(values):
    return sum(values, 0.0) / len(values)

def map(request, id_string):
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

def send_file(path, content_type):
    """
    Send a file through Django without loading the whole file into
    memory at once. The FileWrapper will turn the file object into an
    iterator for chunks of 8KB.
    """
    wrapper = FileWrapper(file(path))
    response = HttpResponse(wrapper, content_type=content_type)
    response['Content-Length'] = os.path.getsize(path)
    return response

@login_required
def csv_export(request, username, id_string):
    dd = DataDictionary.objects.get(id_string=id_string,
                                    user=request.user)
    writer = DataDictionaryWriter(dd)
    file_path = writer.get_default_file_path()
    writer.write_to_file(file_path)
    return send_file(path=file_path, content_type="application/csv")

def xls_export(request, username, id_string):
    dd = DataDictionary.objects.get(id_string=id_string,
                                    user=request.user)
    ddw = XlsWriter()
    ddw.set_data_dictionary(dd)
    temp_file = ddw.save_workbook_to_file()
    response = HttpResponse(mimetype='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=%s.xls' % id_string
    response.write(temp_file.getvalue())
    temp_file.close()
    return response

