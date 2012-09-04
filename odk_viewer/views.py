from collections import defaultdict
from datetime import date
import json
import os
import urllib2
import zipfile
from tempfile import NamedTemporaryFile
from time import strftime, strptime
from urlparse import urlparse

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.files.storage import get_storage_class
from django.core.urlresolvers import reverse
from django.http import HttpResponseForbidden,\
    HttpResponseRedirect, HttpResponseNotFound, HttpResponseBadRequest,\
    HttpResponse
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.utils import simplejson
from pyxform import Section, Question

from main.models import UserProfile, MetaData, TokenStorageModel
from odk_logger.models import XForm, Instance, Attachment
from odk_logger.views import download_jsonform
from odk_logger.xform_instance_parser import xform_instance_to_dict
from odk_viewer.models import DataDictionary, ParsedInstance
from pyxform import Section, Question
from odk_viewer.pandas_mongo_bridge import XLSDataFrameBuilder,\
    CSVDataFrameBuilder, NoRecordsFoundError
from csv_writer import CsvWriter
from utils.image_tools import image_url
from xls_writer import XlsWriter
from utils.logger_tools import response_with_mimetype_and_name,\
    disposition_ext_and_date, round_down_geopoint
from utils.viewer_tools import image_urls, image_urls_for_form
from utils.user_auth import has_permission, get_xform_and_perms
from utils.google import google_export_xls, redirect_uri
# TODO: using from main.views import api breaks the application, why?
import main


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
                    HttpResponseBadRequest(
                        _(u'Start time format must be YY_MM_DD_hh_mm_ss'))
                    ]
        dd.surveys_for_export = \
            lambda d: d.surveys.filter(date_created__gte=start)
    if request.GET.get('end'):
        try:
            end = encode(request.GET['end'])
        except ValueError:
            # bad format
            return [False,
                    HttpReponseBadRequest(
                        _(u'End time format must be YY_MM_DD_hh_mm_ss'))
                    ]
        dd.surveys_for_export = \
            lambda d: d.surveys.filter(date_created__lte=end)
    if start and end:
        dd.surveys_for_export = \
            lambda d: d.surveys.filter(date_created__lte=end,
                                       date_created__gte=start)
    return [True, dd]


def parse_label_for_display(pi, xpath):
    label = pi.data_dictionary.get_label(xpath)
    if not type(label) == dict:
        label = {'Unknown': label}
    return label.items()


def average(values):
    if len(values):
        return sum(values, 0.0) / len(values)
    return None


def map_view(request, username, id_string):
    owner = get_object_or_404(User, username=username)
    xform = get_object_or_404(XForm, id_string=id_string, user=owner)
    if not has_permission(xform, owner, request):
        return HttpResponseForbidden(_(u'Not shared.'))
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
    context.center = json.dumps(center)
    context.form_view = True
    context.jsonform_url = reverse(download_jsonform,
                                   kwargs={"username": username,
                                           "id_string": id_string})
    context.mongo_api_url = reverse(main.views.api,
                                    kwargs={"username": username,
                                            "id_string": id_string})
    context.mapbox_layer = MetaData.mapbox_layer_upload(xform)
    return render_to_response('map.html', context_instance=context)


# TODO: do a good job of displaying hierarchical data
def survey_responses(request, instance_id):
    pi = get_object_or_404(ParsedInstance, instance=instance_id)
    xform, is_owner, can_edit, can_view = \
        get_xform_and_perms(pi.instance.user.username,
                            pi.instance.xform.id_string, request)
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
    owner = get_object_or_404(User, username=username)
    xform = get_object_or_404(XForm, id_string=id_string, user=owner)
    if not has_permission(xform, owner, request):
        return HttpResponseForbidden(_(u'Not shared.'))
    query = request.GET.get("query")
    csv_dataframe_builder = CSVDataFrameBuilder(username, id_string, query)
    try:
        temp_file = NamedTemporaryFile(suffix=".csv")
        csv_dataframe_builder.export_to(temp_file)
        if request.GET.get('raw'):
            id_string = None
        response = response_with_mimetype_and_name('application/csv', id_string,
                                                   extension='csv')
        temp_file.seek(0)
        response.write(temp_file.read())
        temp_file.seek(0, os.SEEK_END)
        response['Content-Length'] = temp_file.tell()
        temp_file.close()
        return response
    except NoRecordsFoundError:
        return HttpResponse(_("No records found to export"))

def xls_export(request, username, id_string):
    owner = get_object_or_404(User, username=username)
    xform = get_object_or_404(XForm, id_string=id_string, user=owner)
    if not has_permission(xform, owner, request):
        return HttpResponseForbidden(_(u'Not shared.'))
    query = request.GET.get("query")
    force_xlsx = request.GET.get('xlsx') == 'true'
    xls_df_builder = XLSDataFrameBuilder(username, id_string, query)
    excel_defs = {
      'xls': {
        'suffix': '.xls',
        'mime_type': 'vnd.ms-excel'
      },
      'xlsx': {
        'suffix': '.xlsx',
        'mime_type': 'vnd.openxmlformats' # TODO: check xlsx mime type
      }
    }
    ext = 'xls' if not force_xlsx else 'xlsx'
    if xls_df_builder.exceeds_xls_limits:
        ext = 'xlsx'
    try:
        temp_file = NamedTemporaryFile(suffix=excel_defs[ext]['suffix'])
        xls_df_builder.export_to(temp_file.name)

        if request.GET.get('raw'):
            id_string = None
        response = response_with_mimetype_and_name(excel_defs[ext]['mime_type'], id_string,
                                                   extension=ext)
        response.write(temp_file.read())
        temp_file.seek(0, os.SEEK_END)
        response['Content-Length'] = temp_file.tell()
        temp_file.close()
        return response
    except NoRecordsFoundError:
        return HttpResponse(_("No records found to export"))

def zip_export(request, username, id_string):
    owner = get_object_or_404(User, username=username)
    xform = get_object_or_404(XForm, id_string=id_string, user=owner)
    if not has_permission(xform, owner, request):
        return HttpResponseForbidden(_(u'Not shared.'))
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
                                               file_path=tmp.name,
                                               use_local_filesystem=True)
    return response


def kml_export(request, username, id_string):
    # read the locations from the database
    context = RequestContext(request)
    context.message = "HELLO!!"
    owner = get_object_or_404(User, username=username)
    xform = get_object_or_404(XForm, id_string=id_string, user=owner)
    if not has_permission(xform, owner, request):
        return HttpResponseForbidden(_(u'Not shared.'))
    dd = DataDictionary.objects.get(id_string=id_string,
                                    user=owner)
    pis = ParsedInstance.objects.filter(instance__user=owner,
                                        instance__xform__id_string=id_string,
                                        lat__isnull=False, lng__isnull=False)
    data_for_template = []

    labels = {}

    def cached_get_labels(xpath):
        if xpath in labels.keys():
            return labels[xpath]
        labels[xpath] = dd.get_label(xpath)
        return labels[xpath]

    for pi in pis:
        # read the survey instances
        data_for_display = pi.to_dict()
        xpaths = data_for_display.keys()
        xpaths.sort(cmp=pi.data_dictionary.get_xpath_cmp())
        label_value_pairs = [
            (cached_get_labels(xpath),
             data_for_display[xpath]) for xpath in xpaths
            if not xpath.startswith(u"_")]
        table_rows = []
        for key, value in label_value_pairs:
            table_rows.append('<tr><td>%s</td><td>%s</td></tr>' % (key, value))
        img_urls = image_urls(pi.instance)
        img_url = img_urls[0] if img_urls else ""
        data_for_template.append({
            'name': id_string,
            'id': pi.id,
            'lat': pi.lat,
            'lng': pi.lng,
            'image_urls': img_urls,
            'table': '<table border="1"><a href="#"><img width="210" '
                     'class="thumbnail" src="%s" alt=""></a>%s'
                     '</table>' % (img_url, ''.join(table_rows))})
    context.data = data_for_template
    response = \
        render_to_response("survey.kml", context_instance=context,
                           mimetype="application/vnd.google-earth.kml+xml")
    response['Content-Disposition'] = \
        disposition_ext_and_date(id_string, 'kml')
    return response


def google_xls_export(request, username, id_string):
    token = None
    if request.user.is_authenticated():
        try:
            ts = TokenStorageModel.objects.get(id=request.user)
        except TokenStorageModel.DoesNotExist:
            pass
        else:
          token = ts.token
    elif request.session.get('access_token'):
        token = request.session.get('access_token')
    if token is None:
        request.session["google_redirect_url"] =  reverse(google_xls_export,
                kwargs={'username': username,
                      'id_string': id_string})
        return HttpResponseRedirect(redirect_uri)
    owner = get_object_or_404(User, username=username)
    xform = get_object_or_404(XForm, id_string=id_string, user=owner)
    if not has_permission(xform, owner, request):
        return HttpResponseForbidden(_(u'Not shared.'))
    valid, dd = dd_for_params(id_string, owner, request)
    if not valid:
        return dd
    ddw = XlsWriter()
    tmp = NamedTemporaryFile(delete=False)
    ddw.set_file(tmp)
    ddw.set_data_dictionary(dd)
    temp_file = ddw.save_workbook_to_file()
    temp_file.close()
    url = google_export_xls(tmp.name, xform.title, token, blob=True)
    os.unlink(tmp.name)
    return HttpResponseRedirect(url)


def data_view(request, username, id_string):
    owner = get_object_or_404(User, username=username)
    xform = get_object_or_404(XForm, id_string=id_string, user=owner)
    if not has_permission(xform, owner, request):
        return HttpResponseForbidden(_(u'Not shared.'))

    context = RequestContext(request)
    context.mongo_api_url = reverse(main.views.api,
                                    kwargs={"username": username,
                                            "id_string": id_string})
    context.jsonform_url = reverse(download_jsonform,
                                   kwargs={"username": username,
                                           "id_string": id_string})
    return render_to_response("data_view.html", context_instance=context)


def attachment_url(request, size='medium'):
    media_file = request.GET.get('media_file')
    # TODO: how to make sure we have the right media file,
    # this assumes duplicates are the same file
    result = Attachment.objects.filter(media_file=media_file)[0:1]
    if result.count() == 0:
        return HttpResponseNotFound(_(u'Attachment not found'))
    attachment = result[0]

    media_url = image_url(attachment, size)
    return redirect(media_url)


def instance(request, username, id_string):
    xform, is_owner, can_edit, can_view = get_xform_and_perms(
        username, id_string, request)
    # no access
    if not (xform.shared_data or can_view or
            request.session.get('public_link')):
        return HttpResponseForbidden(_(u'Not shared.'))

    return render_to_response('instance.html', {
        'username': username,
        'id_string': id_string,
        'xform': xform,
        'can_edit': can_edit
    })
