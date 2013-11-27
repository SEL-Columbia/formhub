import json
import os
from datetime import datetime
from tempfile import NamedTemporaryFile
from time import strftime, strptime

from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponseForbidden,\
    HttpResponseRedirect, HttpResponseNotFound, HttpResponseBadRequest,\
    HttpResponse
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.core.files.storage import FileSystemStorage
from django.core.files.storage import get_storage_class

from main.models import UserProfile, MetaData, TokenStorageModel
from odk_logger.models import XForm, Attachment
from odk_logger.views import download_jsonform
from odk_viewer.models import DataDictionary, ParsedInstance
from odk_viewer.pandas_mongo_bridge import NoRecordsFoundError
from utils.image_tools import image_url
from xls_writer import XlsWriter
from utils.logger_tools import response_with_mimetype_and_name,\
    disposition_ext_and_date
from utils.viewer_tools import image_urls
from odk_viewer.tasks import create_async_export
from utils.user_auth import has_permission, get_xform_and_perms,\
    helper_auth_helper
from utils.google import google_export_xls, redirect_uri
# TODO: using from main.views import api breaks the application, why?
from odk_viewer.models import Export
from utils.export_tools import generate_export, should_create_new_export
from utils.export_tools import kml_export_data
from utils.export_tools import newset_export_for
from utils.viewer_tools import export_def_from_filename
from utils.viewer_tools import create_attachments_zipfile
from utils.log import audit_log, Actions
from common_tags import SUBMISSION_TIME


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
                    HttpResponseBadRequest(
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


def map_view(request, username, id_string, template='map.html'):
    owner = get_object_or_404(User, username=username)
    xform = get_object_or_404(XForm, id_string=id_string, user=owner)
    if not has_permission(xform, owner, request):
        return HttpResponseForbidden(_(u'Not shared.'))
    context = RequestContext(request)
    context.content_user = owner
    context.xform = xform
    context.profile, created = UserProfile.objects.get_or_create(user=owner)

    context.form_view = True
    context.jsonform_url = reverse(download_jsonform,
                                   kwargs={"username": username,
                                           "id_string": id_string})
    context.enketo_edit_url = reverse('edit_data',
                                      kwargs={"username": username,
                                              "id_string": id_string,
                                              "data_id": 0})
    context.enketo_add_url = reverse('enter_data',
                                     kwargs={"username": username,
                                             "id_string": id_string})

    context.enketo_add_with_url = reverse('add_submission_with',
                                          kwargs={"username": username,
                                                  "id_string": id_string})
    context.mongo_api_url = reverse('mongo_view_api',
                                    kwargs={"username": username,
                                            "id_string": id_string})
    context.delete_data_url = reverse('delete_data',
                                      kwargs={"username": username,
                                              "id_string": id_string})
    context.mapbox_layer = MetaData.mapbox_layer_upload(xform)
    audit = {
        "xform": xform.id_string
    }
    audit_log(Actions.FORM_MAP_VIEWED, request.user, owner,
              _("Requested map on '%(id_string)s'.")
              % {'id_string': xform.id_string}, audit, request)
    return render_to_response(template, context_instance=context)


def map_embed_view(request, username, id_string):
    return map_view(request, username, id_string, template='map_embed.html')


def add_submission_with(request, username, id_string):

    import uuid
    import requests

    from django.conf import settings
    from django.template import loader, Context
    from dpath import util as dpath_util
    from dict2xml import dict2xml

    def geopoint_xpaths(username, id_string):
        d = DataDictionary.objects.get(user__username=username, id_string=id_string)
        return [e.get_abbreviated_xpath()
                for e in d.get_survey_elements()
                if e.bind.get(u'type') == u'geopoint']

    value = request.GET.get('coordinates')
    xpaths = geopoint_xpaths(username, id_string)
    xml_dict = {}
    for path in xpaths:
        dpath_util.new(xml_dict, path, value)

    context = {'username': username,
               'id_string': id_string,
               'xml_content': dict2xml(xml_dict)}
    instance_xml = loader.get_template("instance_add.xml").render(Context(context))

    url = settings.ENKETO_API_INSTANCE_IFRAME_URL
    return_url = reverse('thank_you_submission', kwargs={"username": username,
                                                         "id_string": id_string})
    if settings.DEBUG:
        openrosa_url = "https://dev.formhub.org/{}".format(username)
    else:
        openrosa_url = request.build_absolute_uri("/{}".format(username))
    payload = {'return_url': return_url,
               'form_id': id_string,
               'server_url': openrosa_url,
               'instance': instance_xml,
               'instance_id': uuid.uuid4().hex}

    r = requests.post(url, data=payload,
                      auth=(settings.ENKETO_API_TOKEN, ''), verify=False)

    return HttpResponse(r.text, mimetype='application/json')


def thank_you_submission(request, username, id_string):
    return HttpResponse("Thank You")


# TODO: do a good job of displaying hierarchical data
def survey_responses(request, instance_id):
    pi = get_object_or_404(ParsedInstance, instance=instance_id)
    xform, is_owner, can_edit, can_view = \
        get_xform_and_perms(pi.instance.user.username,
                            pi.instance.xform.id_string, request)
    # no access
    if not (xform.shared_data or can_view or
            request.session.get('public_link') == xform.uuid):
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
    audit = {
        "xform": xform.id_string,
        "instance_id": instance_id
    }
    audit_log(
        Actions.FORM_DATA_VIEWED, request.user, xform.user,
        _("Requested survey with id '%(instance_id)s' on '%(id_string)s'.") %
        {
            'id_string': xform.id_string,
            'instance_id': instance_id
        }, audit, request)
    return render_to_response('survey.html', {
        'label_value_pairs': label_value_pairs,
        'image_urls': image_urls(pi.instance),
        'languages': languages,
        'default_language': languages[0][0]
    })


def data_export(request, username, id_string, export_type):
    owner = get_object_or_404(User, username=username)
    xform = get_object_or_404(XForm, id_string=id_string, user=owner)
    helper_auth_helper(request)
    if not has_permission(xform, owner, request):
        return HttpResponseForbidden(_(u'Not shared.'))
    query = request.GET.get("query")
    extension = export_type

    # check if we should force xlsx
    force_xlsx = request.GET.get('xls') != 'true'
    if export_type == Export.XLS_EXPORT and force_xlsx:
        extension = 'xlsx'
    elif export_type == Export.CSV_ZIP_EXPORT:
        extension = 'zip'

    audit = {
        "xform": xform.id_string,
        "export_type": export_type
    }
    # check if we need to re-generate,
    # we always re-generate if a filter is specified
    if should_create_new_export(xform, export_type) or query or\
                    'start' in request.GET or 'end' in request.GET:
        format_date_for_mongo = lambda x, datetime: datetime.strptime(
            x, '%y_%m_%d_%H_%M_%S').strftime('%Y-%m-%dT%H:%M:%S')
        # check for start and end params
        if 'start' in request.GET or 'end' in request.GET:
            if not query:
                query = '{}'
            query = json.loads(query)
            query[SUBMISSION_TIME] = {}
            try:
                if request.GET.get('start'):
                    query[SUBMISSION_TIME]['$gte'] = format_date_for_mongo(
                        request.GET['start'], datetime)
                if request.GET.get('end'):
                    query[SUBMISSION_TIME]['$lte'] = format_date_for_mongo(
                        request.GET['end'], datetime)
            except ValueError:
                return HttpResponseBadRequest(
                    _("Dates must be in the format YY_MM_DD_hh_mm_ss"))
            else:
                query = json.dumps(query)
        try:
            export = generate_export(
                export_type, extension, username, id_string, None, query)
            audit_log(
                Actions.EXPORT_CREATED, request.user, owner,
                _("Created %(export_type)s export on '%(id_string)s'.") %
                {
                    'id_string': xform.id_string,
                    'export_type': export_type.upper()
                }, audit, request)
        except NoRecordsFoundError:
            return HttpResponseNotFound(_("No records found to export"))
    else:
        export = newset_export_for(xform, export_type)

    # log download as well
    audit_log(
        Actions.EXPORT_DOWNLOADED, request.user, owner,
        _("Downloaded %(export_type)s export on '%(id_string)s'.") %
        {
            'id_string': xform.id_string,
            'export_type': export_type.upper()
        }, audit, request)

    if not export.filename:
        # tends to happen when using newset_export_for.
        return HttpResponseNotFound("File does not exist!")
    # get extension from file_path, exporter could modify to
    # xlsx if it exceeds limits
    path, ext = os.path.splitext(export.filename)
    ext = ext[1:]
    if request.GET.get('raw'):
        id_string = None
    response = response_with_mimetype_and_name(
        Export.EXPORT_MIMES[ext], id_string, extension=ext,
        file_path=export.filepath)
    return response


@require_POST
def create_export(request, username, id_string, export_type):
    owner = get_object_or_404(User, username=username)
    xform = get_object_or_404(XForm, id_string=id_string, user=owner)
    if not has_permission(xform, owner, request):
        return HttpResponseForbidden(_(u'Not shared.'))

    query = request.POST.get("query")
    force_xlsx = request.POST.get('xls') != 'true'

    # export options
    group_delimiter = request.POST.get("options[group_delimiter]", '/')
    if group_delimiter not in ['.', '/']:
        return HttpResponseBadRequest(
            _("%s is not a valid delimiter" % group_delimiter))

    # default is True, so when dont_.. is yes
    # split_select_multiples becomes False
    split_select_multiples = request.POST.get(
        "options[dont_split_select_multiples]", "no") == "no"

    options = {
        'group_delimiter': group_delimiter,
        'split_select_multiples': split_select_multiples
    }

    try:
        create_async_export(xform, export_type, query, force_xlsx, options)
    except Export.ExportTypeError:
        return HttpResponseBadRequest(
            _("%s is not a valid export type" % export_type))
    else:
        audit = {
            "xform": xform.id_string,
            "export_type": export_type
        }
        audit_log(
            Actions.EXPORT_CREATED, request.user, owner,
            _("Created %(export_type)s export on '%(id_string)s'.") %
            {
                'export_type': export_type.upper(),
                'id_string': xform.id_string,
            }, audit, request)
        return HttpResponseRedirect(reverse(
            export_list,
            kwargs={
                "username": username,
                "id_string": id_string,
                "export_type": export_type
            })
        )


def _get_google_token(request, redirect_to_url):
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
        request.session["google_redirect_url"] = redirect_to_url
        return HttpResponseRedirect(redirect_uri)
    return token


def export_list(request, username, id_string, export_type):
    if export_type == Export.GDOC_EXPORT:
        redirect_url = reverse(
            export_list,
            kwargs={
                'username': username, 'id_string': id_string,
                'export_type': export_type})
        token = _get_google_token(request, redirect_url)
        if isinstance(token, HttpResponse):
            return token
    owner = get_object_or_404(User, username=username)
    xform = get_object_or_404(XForm, id_string=id_string, user=owner)
    if not has_permission(xform, owner, request):
        return HttpResponseForbidden(_(u'Not shared.'))

    if should_create_new_export(xform, export_type):
        try:
            create_async_export(
                xform, export_type, query=None, force_xlsx=True)
        except Export.ExportTypeError:
            return HttpResponseBadRequest(
                _("%s is not a valid export type" % export_type))

    context = RequestContext(request)
    context.username = owner.username
    context.xform = xform
    # TODO: better output e.g. Excel instead of XLS
    context.export_type = export_type
    context.export_type_name = Export.EXPORT_TYPE_DICT[export_type]
    exports = Export.objects.filter(xform=xform, export_type=export_type)\
        .order_by('-created_on')
    context.exports = exports
    return render_to_response('export_list.html', context_instance=context)


def export_progress(request, username, id_string, export_type):
    owner = get_object_or_404(User, username=username)
    xform = get_object_or_404(XForm, id_string=id_string, user=owner)
    if not has_permission(xform, owner, request):
        return HttpResponseForbidden(_(u'Not shared.'))

    # find the export entry in the db
    export_ids = request.GET.getlist('export_ids')
    exports = Export.objects.filter(xform=xform, id__in=export_ids)
    statuses = []
    for export in exports:
        status = {
            'complete': False,
            'url': None,
            'filename': None,
            'export_id': export.id
        }

        if export.status == Export.SUCCESSFUL:
            status['url'] = reverse(export_download, kwargs={
                'username': owner.username,
                'id_string': xform.id_string,
                'export_type': export.export_type,
                'filename': export.filename
            })
            status['filename'] = export.filename
            if export.export_type == Export.GDOC_EXPORT and \
                    export.export_url is None:
                redirect_url = reverse(
                    export_progress,
                    kwargs={
                        'username': username, 'id_string': id_string,
                        'export_type': export_type})
                token = _get_google_token(request, redirect_url)
                if isinstance(token, HttpResponse):
                    return token
                status['url'] = None
                try:
                    url = google_export_xls(
                        export.full_filepath, xform.title, token, blob=True)
                except Exception, e:
                    status['error'] = True
                    status['message'] = e.message
                else:
                    export.export_url = url
                    export.save()
                    status['url'] = url
        # mark as complete if it either failed or succeeded but NOT pending
        if export.status == Export.SUCCESSFUL \
                or export.status == Export.FAILED:
            status['complete'] = True
        statuses.append(status)

    return HttpResponse(
        json.dumps(statuses), mimetype='application/json')


def export_download(request, username, id_string, export_type, filename):
    owner = get_object_or_404(User, username=username)
    xform = get_object_or_404(XForm, id_string=id_string, user=owner)
    helper_auth_helper(request)
    if not has_permission(xform, owner, request):
        return HttpResponseForbidden(_(u'Not shared.'))

    # find the export entry in the db
    export = get_object_or_404(Export, xform=xform, filename=filename)

    if export_type == Export.GDOC_EXPORT and export.export_url is not None:
        return HttpResponseRedirect(export.export_url)

    ext, mime_type = export_def_from_filename(export.filename)

    audit = {
        "xform": xform.id_string,
        "export_type": export.export_type
    }
    audit_log(
        Actions.EXPORT_DOWNLOADED, request.user, owner,
        _("Downloaded %(export_type)s export '%(filename)s' "
          "on '%(id_string)s'.") %
        {
            'export_type': export.export_type.upper(),
            'filename': export.filename,
            'id_string': xform.id_string,
        }, audit, request)
    if request.GET.get('raw'):
        id_string = None

    default_storage = get_storage_class()()
    if not isinstance(default_storage, FileSystemStorage):
        return HttpResponseRedirect(default_storage.url(export.filepath))
    basename = os.path.splitext(export.filename)[0]
    response = response_with_mimetype_and_name(
        mime_type, name=basename, extension=ext,
        file_path=export.filepath, show_date=False)
    return response


@require_POST
def delete_export(request, username, id_string, export_type):
    owner = get_object_or_404(User, username=username)
    xform = get_object_or_404(XForm, id_string=id_string, user=owner)
    if not has_permission(xform, owner, request):
        return HttpResponseForbidden(_(u'Not shared.'))

    export_id = request.POST.get('export_id')

    # find the export entry in the db
    export = get_object_or_404(Export, id=export_id)

    export.delete()
    audit = {
        "xform": xform.id_string,
        "export_type": export.export_type
    }
    audit_log(
        Actions.EXPORT_DOWNLOADED, request.user, owner,
        _("Deleted %(export_type)s export '%(filename)s'"
          " on '%(id_string)s'.") %
        {
            'export_type': export.export_type.upper(),
            'filename': export.filename,
            'id_string': xform.id_string,
        }, audit, request)
    return HttpResponseRedirect(reverse(
        export_list,
        kwargs={
            "username": username,
            "id_string": id_string,
            "export_type": export_type
        }))


def zip_export(request, username, id_string):
    owner = get_object_or_404(User, username=username)
    xform = get_object_or_404(XForm, id_string=id_string, user=owner)
    helper_auth_helper(request)
    if not has_permission(xform, owner, request):
        return HttpResponseForbidden(_(u'Not shared.'))
    if request.GET.get('raw'):
        id_string = None
    attachments = Attachment.objects.filter(instance__xform=xform)
    zip_file = create_attachments_zipfile(attachments)
    audit = {
        "xform": xform.id_string,
        "export_type": Export.ZIP_EXPORT
    }
    audit_log(
        Actions.EXPORT_CREATED, request.user, owner,
        _("Created ZIP export on '%(id_string)s'.") %
        {
            'id_string': xform.id_string,
        }, audit, request)
    # log download as well
    audit_log(
        Actions.EXPORT_DOWNLOADED, request.user, owner,
        _("Downloaded ZIP export on '%(id_string)s'.") %
        {
            'id_string': xform.id_string,
        }, audit, request)
    if request.GET.get('raw'):
        id_string = None
    response = response_with_mimetype_and_name('zip', id_string,
                                               file_path=zip_file,
                                               use_local_filesystem=True)
    return response


def kml_export(request, username, id_string):
    # read the locations from the database
    context = RequestContext(request)
    context.message = "HELLO!!"
    owner = get_object_or_404(User, username=username)
    xform = get_object_or_404(XForm, id_string=id_string, user=owner)
    helper_auth_helper(request)
    if not has_permission(xform, owner, request):
        return HttpResponseForbidden(_(u'Not shared.'))
    context.data = kml_export_data(id_string, user=owner)
    response = \
        render_to_response("survey.kml", context_instance=context,
                           mimetype="application/vnd.google-earth.kml+xml")
    response['Content-Disposition'] = \
        disposition_ext_and_date(id_string, 'kml')
    audit = {
        "xform": xform.id_string,
        "export_type": Export.KML_EXPORT
    }
    audit_log(
        Actions.EXPORT_CREATED, request.user, owner,
        _("Created KML export on '%(id_string)s'.") %
        {
            'id_string': xform.id_string,
        }, audit, request)
    # log download as well
    audit_log(
        Actions.EXPORT_DOWNLOADED, request.user, owner,
        _("Downloaded KML export on '%(id_string)s'.") %
        {
            'id_string': xform.id_string,
        }, audit, request)
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
        request.session["google_redirect_url"] = reverse(
            google_xls_export,
            kwargs={'username': username, 'id_string': id_string})
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
    audit = {
        "xform": xform.id_string,
        "export_type": "google"
    }
    audit_log(
        Actions.EXPORT_CREATED, request.user, owner,
        _("Created Google Docs export on '%(id_string)s'.") %
        {
            'id_string': xform.id_string,
        }, audit, request)
    return HttpResponseRedirect(url)


def data_view(request, username, id_string):
    owner = get_object_or_404(User, username=username)
    xform = get_object_or_404(XForm, id_string=id_string, user=owner)
    if not has_permission(xform, owner, request):
        return HttpResponseForbidden(_(u'Not shared.'))

    context = RequestContext(request)
    context.owner = owner
    context.xform = xform
    audit = {
        "xform": xform.id_string,
    }
    audit_log(
        Actions.FORM_DATA_VIEWED, request.user, owner,
        _("Requested data view for '%(id_string)s'.") %
        {
            'id_string': xform.id_string,
        }, audit, request)
    return render_to_response("data_view.html", context_instance=context)


def attachment_url(request, size='medium'):
    media_file = request.GET.get('media_file')
    # TODO: how to make sure we have the right media file,
    # this assumes duplicates are the same file
    result = Attachment.objects.filter(media_file=media_file)[0:1]
    if result.count() == 0:
        return HttpResponseNotFound(_(u'Attachment not found'))
    attachment = result[0]
    if not attachment.mimetype.startswith('image'):
        return redirect(attachment.media_file.url)
    try:
        media_url = image_url(attachment, size)
    except:
        # TODO: log this somewhere
        # image not found, 404, S3ResponseError timeouts
        pass
    else:
        if media_url:
            return redirect(media_url)
    return HttpResponseNotFound(_(u'Error: Attachment not found'))


def instance(request, username, id_string):
    xform, is_owner, can_edit, can_view = get_xform_and_perms(
        username, id_string, request)
    # no access
    if not (xform.shared_data or can_view or
            request.session.get('public_link') == xform.uuid):
        return HttpResponseForbidden(_(u'Not shared.'))

    context = RequestContext(request)

    audit = {
        "xform": xform.id_string,
    }
    audit_log(
        Actions.FORM_DATA_VIEWED, request.user, xform.user,
        _("Requested instance view for '%(id_string)s'.") %
        {
            'id_string': xform.id_string,
        }, audit, request)
    return render_to_response('instance.html', {
        'username': username,
        'id_string': id_string,
        'xform': xform,
        'can_edit': can_edit
    }, context_instance=context)
