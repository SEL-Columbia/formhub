from datetime import datetime
from django.contrib.contenttypes.models import ContentType
import os
import urllib2
import json
from django import forms
from django.core.urlresolvers import reverse
from django.core.files.storage import default_storage, get_storage_class
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse, HttpResponseBadRequest, \
    HttpResponseRedirect, HttpResponseNotAllowed, Http404, \
    HttpResponseForbidden, HttpResponseNotFound, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404
from django.template import loader, RequestContext
from django.utils import simplejson
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.gzip import gzip_page
from google_doc import GoogleDoc
from guardian.shortcuts import assign, remove_perm, get_users_with_perms

from main.forms import UserProfileForm, FormLicenseForm, DataLicenseForm,\
    SupportDocForm, QuickConverterFile, QuickConverterURL, QuickConverter,\
    SourceForm, PermissionForm, MediaForm, MapboxLayerForm
from main.models import UserProfile, MetaData
from odk_logger.models import Instance, XForm
from odk_logger.views import enter_data
from odk_viewer.models import DataDictionary, ParsedInstance
from odk_viewer.models.data_dictionary import upload_to
from odk_viewer.models.parsed_instance import GLOBAL_SUBMISSION_STATS,\
    DATETIME_FORMAT
from odk_viewer.views import image_urls_for_form, survey_responses, \
    attachment_url
from stats.models import StatsCount
from stats.tasks import stat_log
from utils.decorators import is_owner
from utils.logger_tools import response_with_mimetype_and_name, publish_form
from utils.user_auth import check_and_set_user, set_profile_data,\
    has_permission, helper_auth_helper, get_xform_and_perms,\
    check_and_set_user_and_form
from utils.log import audit_log, Actions
from main.models import AuditLog

from utils.viewer_tools import enketo_url
from utils.qrcode import generate_qrcode

def home(request):
    if request.user.username:
        return HttpResponseRedirect(
            reverse(profile, kwargs={'username': request.user.username}))
    context = RequestContext(request)
    submission_count = StatsCount.stats.count(GLOBAL_SUBMISSION_STATS)
    if not submission_count:
        submission_count = Instance.objects.count()
        stat_log(GLOBAL_SUBMISSION_STATS, submission_count)
    context.num_forms = submission_count
    context.num_users = User.objects.count()
    context.num_shared_forms = XForm.objects.filter(shared__exact=1).count()
    return render_to_response('home.html', context_instance=context)


@login_required
def login_redirect(request):
    return HttpResponseRedirect(reverse(profile,
                                kwargs={'username': request.user.username}))


@require_POST
@login_required
def clone_xlsform(request, username):
    """
    Copy a public/Shared form to a users list of forms.
    Eliminates the need to download Excel File and upload again.
    """
    to_username = request.user.username
    context = RequestContext(request)
    context.message = {'type': None, 'text': '....'}

    def set_form():
        form_owner = request.POST.get('username')
        id_string = request.POST.get('id_string')
        xform = XForm.objects.get(user__username=form_owner,
                                  id_string=id_string)
        if len(id_string) > 0 and id_string[0].isdigit():
            id_string = '_' + id_string
        path = xform.xls.name
        if default_storage.exists(path):
            xls_file = upload_to(None, '%s%s.xls' % (
                                 id_string, XForm.CLONED_SUFFIX), to_username)
            xls_data = default_storage.open(path)
            xls_file = default_storage.save(xls_file, xls_data)
            context.message = u'%s-%s' % (form_owner, xls_file)
            survey = DataDictionary.objects.create(
                user=request.user,
                xls=xls_file
            ).survey
            # log to cloner's account
            audit = {}
            audit_log(
                Actions.FORM_CLONED, request.user, request.user,
                _("Cloned form '%(id_string)s'.") %
                {
                    'id_string': survey.id_string,
                }, audit, request)
            clone_form_url = reverse(show, kwargs={'username': to_username,'id_string': xform.id_string + XForm.CLONED_SUFFIX })
            return {
                'type': 'alert-success',
                'text': _(u'Successfully cloned to %(form_url)s into your '
                          u'%(profile_url)s') % {
                              'form_url': u'<a href="%(url)s">%(id_string)s</a> ' % {
                                'id_string': survey.id_string,
                                'url': clone_form_url
                              },
                              'profile_url': u'<a href="%s">profile</a>.' %
                              reverse(profile,
                                      kwargs={'username': to_username})
                          }
            }
    context.message = publish_form(set_form)
    if request.is_ajax():
        res = loader.render_to_string(
            'message.html',
            context_instance=context).replace("'", r"\'").replace('\n', '')
        return HttpResponse(
            "$('#mfeedback').html('%s').show();" % res)
    else:
        return HttpResponse(context.message['text'])


def profile(request, username):
    context = RequestContext(request)
    content_user = get_object_or_404(User, username=username)
    context.form = QuickConverter()
    # xlsform submission...
    if request.method == 'POST' and request.user.is_authenticated():
        def set_form():
            form = QuickConverter(request.POST, request.FILES)
            survey = form.publish(request.user).survey
            audit = {}
            audit_log(
                Actions.FORM_PUBLISHED, request.user, content_user,
                _("Published form '%(id_string)s'.") %
                {
                    'id_string': survey.id_string,
                }, audit, request)
            enketo_webform_url = reverse(
                enter_data,
                kwargs={'username': username, 'id_string': survey.id_string}
            )
            return {
                'type': 'alert-success',
                'text': _(u'Successfully published %(form_id)s.'
                          u' <a href="%(form_url)s">Enter Web Form</a>')
                        % {'form_id': survey.id_string,
                            'form_url': enketo_webform_url}
            }
        context.message = publish_form(set_form)

    # profile view...
    # for the same user -> dashboard
    if content_user == request.user:
        context.show_dashboard = True
        context.user_surveys = content_user.surveys.count()
        context.all_forms = content_user.xforms.count()
        context.form = QuickConverterFile()
        context.form_url = QuickConverterURL()
        context.odk_url = request.build_absolute_uri(
            "/%s" % request.user.username)
        crowdforms = XForm.objects.filter(
            metadata__data_type=MetaData.CROWDFORM_USERS,
            metadata__data_value=username
        )
        context.crowdforms = crowdforms
        # forms shared with user
        xfct = ContentType.objects.get(app_label='odk_logger', model='xform')
        fsw = {}
        for xf in content_user.userobjectpermission_set\
                .filter(content_type=xfct):
            if isinstance(xf.content_object, XForm):
                fsw[xf.content_object.pk] = xf.content_object
        context.forms_shared_with = list(fsw.values())
    # for any other user -> profile
    set_profile_data(context, content_user)
    return render_to_response("profile.html", context_instance=context)


def members_list(request):
    context = RequestContext(request)
    users = User.objects.all()
    context.template = 'people.html'
    context.users = users
    return render_to_response("people.html", context_instance=context)


@login_required
def profile_settings(request, username):
    context = RequestContext(request)
    content_user = check_and_set_user(request, username)
    context.content_user = content_user
    profile, created = UserProfile.objects.get_or_create(user=content_user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            # get user
            # user.email = cleaned_email
            form.instance.user.email = form.cleaned_data['email']
            form.instance.user.save()
            form.save()
            # todo: add string rep. of settings to see what changed
            audit = {}
            audit_log(
                Actions.PROFILE_SETTINGS_UPDATED, request.user, content_user,
                _("Profile settings updated."), audit, request)
            return HttpResponseRedirect(reverse(
                public_profile, kwargs={'username': request.user.username}
            ))
    else:
        form = UserProfileForm(
            instance=profile, initial={"email": content_user.email})
    return render_to_response("settings.html", {'form': form},
                              context_instance=context)


@require_GET
def public_profile(request, username):
    content_user = check_and_set_user(request, username)
    if isinstance(content_user, HttpResponseRedirect):
        return content_user
    context = RequestContext(request)
    set_profile_data(context, content_user)
    context.is_owner = request.user == content_user
    audit = {}
    audit_log(
        Actions.PUBLIC_PROFILE_ACCESSED, request.user, content_user,
        _("Public profile accessed."), audit, request)
    return render_to_response("profile.html", context_instance=context)


@login_required
def dashboard(request):
    context = RequestContext(request)
    context.form = QuickConverter()
    content_user = request.user
    set_profile_data(context, content_user)
    context.odk_url = request.build_absolute_uri("/%s" % request.user.username)
    return render_to_response("dashboard.html", context_instance=context)


@require_GET
def show(request, username=None, id_string=None, uuid=None):
    if uuid:
        xform = get_object_or_404(XForm, uuid=uuid)
        request.session['public_link'] = MetaData.public_link(xform)
        return HttpResponseRedirect(reverse(show, kwargs={
            'username': xform.user.username,
            'id_string': xform.id_string
        }))
    xform, is_owner, can_edit, can_view = get_xform_and_perms(
        username, id_string, request)
    # no access
    if not (xform.shared or can_view or request.session.get('public_link')):
        return HttpResponseRedirect(reverse(home))
    context = RequestContext(request)
    context.cloned = len(
        XForm.objects.filter(user__username=request.user.username,
                             id_string=id_string + XForm.CLONED_SUFFIX)
    ) > 0
    context.public_link = MetaData.public_link(xform)
    context.is_owner = is_owner
    context.can_edit = can_edit
    context.can_view = can_view or request.session.get('public_link')
    context.xform = xform
    context.content_user = xform.user
    context.base_url = "https://%s" % request.get_host()
    context.source = MetaData.source(xform)
    context.form_license = MetaData.form_license(xform).data_value
    context.data_license = MetaData.data_license(xform).data_value
    context.supporting_docs = MetaData.supporting_docs(xform)
    context.media_upload = MetaData.media_upload(xform)
    context.mapbox_layer = MetaData.mapbox_layer_upload(xform)
    if is_owner:
        context.form_license_form = FormLicenseForm(
            initial={'value': context.form_license})
        context.data_license_form = DataLicenseForm(
            initial={'value': context.data_license})
        context.doc_form = SupportDocForm()
        context.source_form = SourceForm()
        context.media_form = MediaForm()
        context.mapbox_layer_form = MapboxLayerForm()
        context.users_with_perms = get_users_with_perms(
            xform,
            attach_perms=True
        ).items()
        context.permission_form = PermissionForm(username)
    user_list = [u.username for u in User.objects.exclude(username=username)]
    context.user_json_list = simplejson.dumps(user_list)
    return render_to_response("show.html", context_instance=context)


@require_GET
def api(request, username=None, id_string=None):
    """
    Returns all results as JSON.  If a parameter string is passed,
    it takes the 'query' parameter, converts this string to a dictionary, an
    that is then used as a MongoDB query string.

    NOTE: only a specific set of operators are allow, currently $or and $and.
    Please send a request if you'd like another operator to be enabled.

    NOTE: Your query must be valid JSON, double check it here,
    http://json.parser.online.fr/

    E.g. api?query='{"last_name": "Smith"}'
    """
    helper_auth_helper(request)
    xform, owner = check_and_set_user_and_form(username, id_string, request)

    if not xform:
        return HttpResponseForbidden(_(u'Not shared.'))

    try:
        args = {
            'username': username,
            'id_string': id_string,
            'query': request.GET.get('query'),
            'fields': request.GET.get('fields'),
            'sort': request.GET.get('sort')
        }
        if 'start' in request.GET:
            args["start"] = int(request.GET.get('start'))
        if 'limit' in request.GET:
            args["limit"] = int(request.GET.get('limit'))
        if 'count' in request.GET:
            args["count"] = True if int(request.GET.get('count')) > 0\
                else False
        cursor = ParsedInstance.query_mongo(**args)
    except ValueError, e:
        return HttpResponseBadRequest(e.__str__())
    records = list(record for record in cursor)
    response_text = simplejson.dumps(records)
    if 'callback' in request.GET and request.GET.get('callback') != '':
        callback = request.GET.get('callback')
        response_text = ("%s(%s)" % (callback, response_text))
    return HttpResponse(response_text, mimetype='application/json')


@require_GET
def public_api(request, username, id_string):
    """
    Returns public information about the form as JSON
    """

    xform = get_object_or_404(XForm,
                              user__username=username, id_string=id_string)

    DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
    exports = {'username': xform.user.username,
               'id_string': xform.id_string,
               'bamboo_dataset': xform.bamboo_dataset,
               'shared': xform.shared,
               'shared_data': xform.shared_data,
               'downloadable': xform.downloadable,
               'is_crowd_form': xform.is_crowd_form,
               'title': xform.title,
               'date_created': xform.date_created.strftime(DATETIME_FORMAT),
               'date_modified': xform.date_modified.strftime(DATETIME_FORMAT),
               'uuid': xform.uuid,
               }
    response_text = simplejson.dumps(exports)
    return HttpResponse(response_text, mimetype='application/json')


@login_required
def edit(request, username, id_string):
    xform = XForm.objects.get(user__username=username, id_string=id_string)
    owner = xform.user

    if request.GET.get('crowdform'):
        crowdform_action = request.GET['crowdform']
        request_username = request.user.username

        # ensure is crowdform
        if xform.is_crowd_form:
            if crowdform_action == 'delete':
                MetaData.objects.get(
                    xform__id_string=id_string,
                    data_value=request_username,
                    data_type=MetaData.CROWDFORM_USERS
                ).delete()
            elif crowdform_action == 'add':
                MetaData.crowdform_users(xform, request_username)

            return HttpResponseRedirect(reverse(profile, kwargs={
                'username': request_username
            }))

    if username == request.user.username or\
            request.user.has_perm('odk_logger.change_xform', xform):
        if request.POST.get('description'):
            audit = {
                'xform': xform.id_string
            }
            audit_log(
                Actions.FORM_UPDATED, request.user, owner,
                _("Description for '%(id_string)s' updated from "
                    "'%(old_description)s' to '%(new_description)s'.") %
                {
                    'id_string': xform.id_string,
                    'old_description': xform.description,
                    'new_description': request.POST['description']
                }, audit, request)
            xform.description = request.POST['description']
        elif request.POST.get('title'):
            audit = {
                'xform': xform.id_string
            }
            audit_log(
                Actions.FORM_UPDATED, request.user, owner,
                _("Title for '%(id_string)s' updated from "
                    "'%(old_title)s' to '%(new_title)s'.") %
                {
                    'id_string': xform.id_string,
                    'old_title': xform.title,
                    'new_title': request.POST.get('title')
                }, audit, request)
            xform.title = request.POST['title']
        elif request.POST.get('toggle_shared'):
            if request.POST['toggle_shared'] == 'data':
                audit = {
                    'xform': xform.id_string
                }
                audit_log(
                    Actions.FORM_UPDATED, request.user, owner,
                    _("Data sharing updated for '%(id_string)s' from "
                        "'%(old_shared)s' to '%(new_shared)s'.") %
                    {
                        'id_string': xform.id_string,
                        'old_shared': _("shared")
                        if xform.shared_data else _("not shared"),
                        'new_shared': _("shared")
                        if not xform.shared_data else _("not shared")
                    }, audit, request)
                xform.shared_data = not xform.shared_data
            elif request.POST['toggle_shared'] == 'form':
                audit = {
                    'xform': xform.id_string
                }
                audit_log(
                    Actions.FORM_UPDATED, request.user, owner,
                    _("Form sharing for '%(id_string)s' updated "
                        "from '%(old_shared)s' to '%(new_shared)s'.") %
                    {
                        'id_string': xform.id_string,
                        'old_shared': _("shared")
                        if xform.shared else _("not shared"),
                        'new_shared': _("shared")
                        if not xform.shared else _("not shared")
                    }, audit, request)
                xform.shared = not xform.shared
            elif request.POST['toggle_shared'] == 'active':
                audit = {
                    'xform': xform.id_string
                }
                audit_log(
                    Actions.FORM_UPDATED, request.user, owner,
                    _("Active status for '%(id_string)s' updated from "
                        "'%(old_shared)s' to '%(new_shared)s'.") %
                    {
                        'id_string': xform.id_string,
                        'old_shared': _("shared")
                        if xform.downloadable else _("not shared"),
                        'new_shared': _("shared")
                        if not xform.downloadable else _("not shared")
                    }, audit, request)
                xform.downloadable = not xform.downloadable
            elif request.POST['toggle_shared'] == 'crowd':
                audit = {
                    'xform': xform.id_string
                }
                audit_log(
                    Actions.FORM_UPDATED, request.user, owner,
                    _("Crowdform status for '%(id_string)s' updated from "
                        "'%(old_status)s' to '%(new_status)s'.") %
                    {
                        'id_string': xform.id_string,
                        'old_status': _("crowdform")
                        if not xform.is_crowd_form else _("not crowdform"),
                        'new_status': _("crowdform")
                        if xform.is_crowd_form else _("not crowdform"),
                    }, audit, request)
                if xform.is_crowd_form:
                    xform.is_crowd_form = False
                else:
                    xform.is_crowd_form = True
                    xform.shared = True
                    xform.shared_data = True
        elif request.POST.get('form-license'):
            audit = {
                'xform': xform.id_string
            }
            audit_log(
                Actions.FORM_UPDATED, request.user, owner,
                _("Form License for '%(id_string)s' updated to "
                    "'%(form_license)s'.") %
                {
                    'id_string': xform.id_string,
                    'form_license': request.POST['form-license'],
                }, audit, request)
            MetaData.form_license(xform, request.POST['form-license'])
        elif request.POST.get('data-license'):
            audit = {
                'xform': xform.id_string
            }
            audit_log(
                Actions.FORM_UPDATED, request.user, owner,
                _("Data license for '%(id_string)s' updated to "
                    "'%(data_license)s'.") %
                {
                    'id_string': xform.id_string,
                    'data_license': request.POST['data-license'],
                }, audit, request)
            MetaData.data_license(xform, request.POST['data-license'])
        elif request.POST.get('source') or request.FILES.get('source'):
            audit = {
                'xform': xform.id_string
            }
            audit_log(
                Actions.FORM_UPDATED, request.user, owner,
                _("Source for '%(id_string)s' updated to '%(source)s'.") %
                {
                    'id_string': xform.id_string,
                    'source': request.POST.get('source'),
                }, audit, request)
            MetaData.source(xform, request.POST.get('source'),
                            request.FILES.get('source'))
        elif request.FILES.get('media'):
            audit = {
                'xform': xform.id_string
            }
            audit_log(
                Actions.FORM_UPDATED, request.user, owner,
                _("Media added to '%(id_string)s'.") %
                {
                    'id_string': xform.id_string
                }, audit, request)
            for aFile in request.FILES.getlist("media"):
              MetaData.media_upload(xform, aFile)
        elif request.POST.get('map_name'):
            mapbox_layer = MapboxLayerForm(request.POST)
            if mapbox_layer.is_valid():
                audit = {
                    'xform': xform.id_string
                }
                audit_log(
                    Actions.FORM_UPDATED, request.user, owner,
                    _("Map layer added to '%(id_string)s'.") %
                    {
                        'id_string': xform.id_string
                    }, audit, request)
                MetaData.mapbox_layer_upload(xform, mapbox_layer.cleaned_data)
        elif request.FILES:
            audit = {
                'xform': xform.id_string
            }
            audit_log(
                Actions.FORM_UPDATED, request.user, owner,
                _("Supporting document added to '%(id_string)s'.") %
                {
                    'id_string': xform.id_string
                }, audit, request)
            MetaData.supporting_docs(xform, request.FILES['doc'])
        xform.update()

        if request.is_ajax():
            return HttpResponse(_(u'Updated succeeded.'))
        else:
            return HttpResponseRedirect(reverse(show, kwargs={
                'username': username,
                'id_string': id_string
            }))
    return HttpResponseForbidden(_(u'Update failed.'))


def getting_started(request):
    context = RequestContext(request)
    context.template = 'getting_started.html'
    return render_to_response('base.html', context_instance=context)


def support(request):
    context = RequestContext(request)
    context.template = 'support.html'
    return render_to_response('base.html', context_instance=context)


def faq(request):
    context = RequestContext(request)
    context.template = 'faq.html'
    return render_to_response('base.html', context_instance=context)


def xls2xform(request):
    context = RequestContext(request)
    context.template = 'xls2xform.html'
    return render_to_response('base.html', context_instance=context)


def tutorial(request):
    context = RequestContext(request)
    context.template = 'tutorial.html'
    username = request.user.username if request.user.username else \
        'your-user-name'
    context.odk_url = request.build_absolute_uri("/%s" % username)
    return render_to_response('base.html', context_instance=context)


def resources(request):
    context = RequestContext(request)
    return render_to_response('resources.html', context_instance=context)


def about_us(request):
    context = RequestContext(request)
    context.a_flatpage = '/about-us/'
    username = request.user.username if request.user.username else \
        'your-user-name'
    context.odk_url = request.build_absolute_uri("/%s" % username)
    return render_to_response('base.html', context_instance=context)


def syntax(request):
    url = 'https://docs.google.com/document/pub?id='\
        '1xD5gSjeyjGjw-V9g5hXx7FWeasRvn-L6zeQJsNeAGBI'
    doc = GoogleDoc(url)
    context = RequestContext(request)
    context.content = doc.to_html()
    return render_to_response('base.html', context_instance=context)


def form_gallery(request):
    """
    Return a list of urls for all the shared xls files. This could be
    made a lot prettier.
    """
    context = RequestContext(request)
    if request.user.is_authenticated():
        context.loggedin_user = request.user
    context.shared_forms = XForm.objects.filter(shared=True)
    # build list of shared forms with cloned suffix
    id_strings_with_cloned_suffix = [
        x.id_string + XForm.CLONED_SUFFIX for x in context.shared_forms
    ]
    # build list of id_strings for forms this user has cloned
    context.cloned = [
        x.id_string.split(XForm.CLONED_SUFFIX)[0]
        for x in XForm.objects.filter(
            user__username=request.user.username,
            id_string__in=id_strings_with_cloned_suffix
        )
    ]
    return render_to_response('form_gallery.html', context_instance=context)


def download_metadata(request, username, id_string, data_id):
    xform = get_object_or_404(XForm,
                              user__username=username, id_string=id_string)
    owner = xform.user
    if username == request.user.username or xform.shared:
        data = get_object_or_404(MetaData, pk=data_id)
        file_path = data.data_file.name
        filename, extension = os.path.splitext(file_path.split('/')[-1])
        extension = extension.strip('.')
        default_storage = get_storage_class()()
        if default_storage.exists(file_path):
            audit = {
                'xform': xform.id_string
            }
            audit_log(
                Actions.FORM_UPDATED, request.user, owner,
                _("Document '%(filename)s' for '%(id_string)s' downloaded.") %
                {
                    'id_string': xform.id_string,
                    'filename': "%s.%s" % (filename, extension)
                }, audit, request)
            response = response_with_mimetype_and_name(
                data.data_file_type,
                filename, extension=extension, show_date=False,
                file_path=file_path)
            return response
        else:
            return HttpResponseNotFound()
    return HttpResponseForbidden(_(u'Permission denied.'))


@login_required()
def delete_metadata(request, username, id_string, data_id):
    xform = get_object_or_404(XForm,
                              user__username=username, id_string=id_string)
    owner = xform.user
    data = get_object_or_404(MetaData, pk=data_id)
    default_storage = get_storage_class()()
    req_username = request.user.username
    if request.GET.get('del', False) and username == req_username:
        try:
            default_storage.delete(data.data_file.name)
            data.delete()
            audit = {
                'xform': xform.id_string
            }
            audit_log(
                Actions.FORM_UPDATED, request.user, owner,
                _("Document '%(filename)s' deleted from '%(id_string)s'.") %
                {
                    'id_string': xform.id_string,
                    'filename': os.path.basename(data.data_file.name)
                }, audit, request)
            return HttpResponseRedirect(reverse(show, kwargs={
                'username': username,
                'id_string': id_string
            }))
        except Exception, e:
            return HttpResponseServerError()
    elif request.GET.get('map_name_del', False) and username == req_username:
        data.delete()
        audit = {
            'xform': xform.id_string
        }
        audit_log(
            Actions.FORM_UPDATED, request.user, owner,
            _("Map layer deleted from '%(id_string)s'.") %
            {
                'id_string': xform.id_string,
            }, audit, request)
        return HttpResponseRedirect(reverse(show, kwargs={
            'username': username,
            'id_string': id_string
        }))
    return HttpResponseForbidden(_(u'Permission denied.'))


def download_media_data(request, username, id_string, data_id):
    xform = get_object_or_404(
        XForm, user__username=username, id_string=id_string)
    owner = xform.user
    data = get_object_or_404(MetaData, id=data_id)
    default_storage = get_storage_class()()
    if request.GET.get('del', False):
        if username == request.user.username:
            try:
                default_storage.delete(data.data_file.name)
                data.delete()
                audit = {
                    'xform': xform.id_string
                }
                audit_log(
                    Actions.FORM_UPDATED, request.user, owner,
                    _("Media download '%(filename)s' deleted from "
                        "'%(id_string)s'.") %
                    {
                        'id_string': xform.id_string,
                        'filename': os.path.basename(data.data_file.name)
                    }, audit, request)
                return HttpResponseRedirect(reverse(show, kwargs={
                    'username': username,
                    'id_string': id_string
                }))
            except Exception, e:
                return HttpResponseServerError()
    else:
        if username:  # == request.user.username or xform.shared:
            file_path = data.data_file.name
            filename, extension = os.path.splitext(file_path.split('/')[-1])
            extension = extension.strip('.')
            if default_storage.exists(file_path):
                audit = {
                    'xform': xform.id_string
                }
                audit_log(
                    Actions.FORM_UPDATED, request.user, owner,
                    _("Media '%(filename)s' downloaded from "
                        "'%(id_string)s'.") %
                    {
                        'id_string': xform.id_string,
                        'filename': os.path.basename(file_path)
                    }, audit, request)
                response = response_with_mimetype_and_name(
                    data.data_file_type,
                    filename, extension=extension, show_date=False,
                    file_path=file_path)
                return response
            else:
                return HttpResponseNotFound()
    return HttpResponseForbidden(_(u'Permission denied.'))


def form_photos(request, username, id_string):
    xform, owner = check_and_set_user_and_form(username, id_string, request)

    if not xform:
        return HttpResponseForbidden(_(u'Not shared.'))

    context = RequestContext(request)
    context.form_view = True
    context.content_user = owner
    context.xform = xform
    image_urls = []

    for instance in xform.surveys.all():
        for attachment in instance.attachments.all():
            # skip if not image e.g video or file
            if not attachment.mimetype.startswith('image'):
                continue

            data = {}

            for i in ['small', 'medium', 'large', 'original']:
                url = reverse(attachment_url, kwargs={'size': i})
                url = '%s?media_file=%s' % (url, attachment.media_file.name)
                data[i] = url

            image_urls.append(data)

    context.images = image_urls
    context.profile, created = UserProfile.objects.get_or_create(user=owner)
    return render_to_response('form_photos.html', context_instance=context)


@require_POST
def set_perm(request, username, id_string):
    xform = get_object_or_404(XForm,
                              user__username=username, id_string=id_string)
    owner = xform.user
    if username != request.user.username\
            and not has_permission(xform, username, request):
        return HttpResponseForbidden(_(u'Permission denied.'))
    try:
        perm_type = request.POST['perm_type']
        for_user = request.POST['for_user']
    except KeyError:
        return HttpResponseBadRequest()
    if perm_type in ['edit', 'view', 'remove']:
        try:
            user = User.objects.get(username=for_user)
        except User.DoesNotExist:
            messages.add_message(
                request, messages.INFO,
                _(u"Wrong username <b>%s</b>." % for_user),
                extra_tags='alert-error')
        else:
            if perm_type == 'edit' and\
                    not user.has_perm('change_xform', xform):
                audit = {
                    'xform': xform.id_string
                }
                audit_log(
                    Actions.FORM_PERMISSIONS_UPDATED, request.user, owner,
                    _("Edit permissions on '%(id_string)s' assigned to "
                        "'%(for_user)s'.") %
                    {
                        'id_string': xform.id_string,
                        'for_user': for_user
                    }, audit, request)
                assign('change_xform', user, xform)
            elif perm_type == 'view' and\
                    not user.has_perm('view_xform', xform):
                audit = {
                    'xform': xform.id_string
                }
                audit_log(
                    Actions.FORM_PERMISSIONS_UPDATED, request.user, owner,
                    _("View permissions on '%(id_string)s' "
                        "assigned to '%(for_user)s'.") %
                    {
                        'id_string': xform.id_string,
                        'for_user': for_user
                    }, audit, request)
                assign('view_xform', user, xform)
            elif perm_type == 'remove':
                audit = {
                    'xform': xform.id_string
                }
                audit_log(
                    Actions.FORM_PERMISSIONS_UPDATED, request.user, owner,
                    _("All permissions on '%(id_string)s' "
                        "removed from '%(for_user)s'.") %
                    {
                        'id_string': xform.id_string,
                        'for_user': for_user
                    }, audit, request)
                remove_perm('change_xform', user, xform)
                remove_perm('view_xform', user, xform)
    elif perm_type == 'link':
        current = MetaData.public_link(xform)
        if for_user == 'all':
            MetaData.public_link(xform, True)
        elif for_user == 'none':
            MetaData.public_link(xform, False)
        elif for_user == 'toggle':
            MetaData.public_link(xform, not current)
        audit = {
            'xform': xform.id_string
        }
        audit_log(
            Actions.FORM_PERMISSIONS_UPDATED, request.user, owner,
            _("Public link on '%(id_string)s' %(action)s.") %
            {
                'id_string': xform.id_string,
                'action': "created"
                if for_user == "all" or
                (for_user == "toggle" and not current) else "removed"
            }, audit, request)
    if request.is_ajax():
        return HttpResponse(
            simplejson.dumps(
                {'status': 'success'}), mimetype='application/json')
    return HttpResponseRedirect(reverse(show, kwargs={
        'username': username,
        'id_string': id_string
    }))


def show_submission(request, username, id_string, uuid):
    xform, is_owner, can_edit, can_view = get_xform_and_perms(
        username, id_string, request)
    owner = xform.user
    # no access
    if not (xform.shared_data or can_view or
            request.session.get('public_link')):
        return HttpResponseRedirect(reverse(home))
    submission = get_object_or_404(Instance, uuid=uuid)
    audit = {
        'xform': xform.id_string
    }
    audit_log(
        Actions.SUBMISSION_ACCESSED, request.user, owner,
        _("Submission '%(uuid)s' on '%(id_string)s' accessed.") %
        {
            'id_string': xform.id_string,
            'uuid': uuid
        }, audit, request)
    return HttpResponseRedirect(reverse(
        survey_responses, kwargs={'instance_id': submission.pk}))


@require_POST
@login_required
def delete_data(request, username=None, id_string=None):
    xform, owner = check_and_set_user_and_form(username, id_string, request)
    response_text = u''
    if not xform:
        return HttpResponseForbidden(_(u'Not shared.'))

    data_id = request.POST.get('id')
    if not data_id:
        return HttpResponseBadRequest(_(u"id must be specified"))

    Instance.set_deleted_at(data_id)
    audit = {
        'xform': xform.id_string
    }
    audit_log(
        Actions.SUBMISSION_DELETED, request.user, owner,
        _("Deleted submission with id '%(record_id)s' "
            "on '%(id_string)s'.") %
        {
            'id_string': xform.id_string,
            'record_id': data_id
        }, audit, request)
    response_text = simplejson.dumps({"success": "Deleted data %s" % data_id})
    if 'callback' in request.GET and request.GET.get('callback') != '':
        callback = request.GET.get('callback')
        response_text = ("%s(%s)" % (callback, response_text))
    return HttpResponse(response_text, mimetype='application/json')


@require_POST
@is_owner
def link_to_bamboo(request, username, id_string):
    xform = get_object_or_404(XForm,
                              user__username=username, id_string=id_string)
    owner = xform.user
    from utils.bamboo import get_new_bamboo_dataset, delete_bamboo_dataset

    audit = {
        'xform': xform.id_string
    }

    # try to delete the dataset first (in case it exists)
    if xform.bamboo_dataset and delete_bamboo_dataset(xform):
        xform.bamboo_dataset = u''
        xform.save()
        audit_log(
            Actions.BAMBOO_LINK_DELETED, request.user, owner,
            _("Bamboo link deleted on '%(id_string)s'.")
            % {'id_string': xform.id_string}, audit, request)

    # create a new one from all the data
    dataset_id = get_new_bamboo_dataset(xform)

    # update XForm
    xform.bamboo_dataset = dataset_id
    xform.save()

    audit_log(
        Actions.BAMBOO_LINK_CREATED, request.user, owner,
        _("Bamboo link created on '%(id_string)s'.") %
        {
            'id_string': xform.id_string,
        }, audit, request)

    return HttpResponseRedirect(reverse(show, kwargs={
        'username': username,
        'id_string': id_string
    }))


@require_POST
@is_owner
def update_xform(request, username, id_string):
    xform = get_object_or_404(
        XForm, user__username=username, id_string=id_string)
    owner = xform.user

    context = RequestContext(request)

    def set_form():
        form = QuickConverter(request.POST, request.FILES)
        survey = form.publish(request.user, id_string).survey
        enketo_webform_url = reverse(
            enter_data,
            kwargs={'username': username, 'id_string': survey.id_string}
        )
        audit = {
            'xform': xform.id_string
        }
        audit_log(
            Actions.FORM_XLS_UPDATED, request.user, owner,
            _("XLS for '%(id_string)s' updated.") %
            {
                'id_string': xform.id_string,
            }, audit, request)
        return {
            'type': 'alert-success',
            'text': _(u'Successfully published %(form_id)s.'
                      u' <a href="%(form_url)s">Enter Web Form</a>')
                    % {'form_id': survey.id_string,
                       'form_url': enketo_webform_url}
        }
    message = publish_form(set_form)
    messages.add_message(
        request, messages.INFO, message['text'], extra_tags=message['type'])
    return HttpResponseRedirect(reverse(show, kwargs={
        'username': username,
        'id_string': id_string
    }))


@is_owner
def activity(request, username):
    owner = get_object_or_404(User, username=username)
    context = RequestContext(request)
    context.user = owner
    return render_to_response('activity.html', context_instance=context)


def activity_fields(request):
    fields = [
        {
            'id': 'created_on',
            'label': _('Performed On'),
            'type': 'datetime',
            'searchable': False
        },
        {
            'id': 'action',
            'label': _('Action'),
            'type': 'string',
            'searchable': True,
            'options': sorted([Actions[e] for e in Actions.enums])
        },
        {
            'id': 'user',
            'label': 'Performed By',
            'type': 'string',
            'searchable': True
        },
        {
            'id': 'msg',
            'label': 'Description',
            'type': 'string',
            'searchable': True
        },
    ]
    response_text = simplejson.dumps(fields)
    return HttpResponse(response_text, mimetype='application/json')


@is_owner
def activity_api(request, username):
    from bson.objectid import ObjectId

    def stringify_unknowns(obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.strftime(DATETIME_FORMAT)
        #raise TypeError
        return None
    try:
        query_args = {
            'username': username,
            'query': json.loads(request.GET.get('query'))
            if request.GET.get('query') else {},
            'fields': json.loads(request.GET.get('fields'))
            if request.GET.get('fields') else [],
            'sort': json.loads(request.GET.get('sort'))
            if request.GET.get('sort') else {}
        }
        if 'start' in request.GET:
            query_args["start"] = int(request.GET.get('start'))
        if 'limit' in request.GET:
            query_args["limit"] = int(request.GET.get('limit'))
        if 'count' in request.GET:
            query_args["count"] = True \
                if int(request.GET.get('count')) > 0 else False
        cursor = AuditLog.query_mongo(**query_args)
    except ValueError, e:
        return HttpResponseBadRequest(e.__str__())
    records = list(record for record in cursor)
    response_text = simplejson.dumps(records, default=stringify_unknowns)
    if 'callback' in request.GET and request.GET.get('callback') != '':
        callback = request.GET.get('callback')
        response_text = ("%s(%s)" % (callback, response_text))
    return HttpResponse(response_text, mimetype='application/json')


def qrcode(request, username, id_string):
    try:
        formhub_url = "http://%s/" % request.META['HTTP_HOST']
    except:
        formhub_url = "http://formhub.org/"
    formhuburl = formhub_url + username
    url = enketo_url(formhuburl, id_string)
    if url:
        image = generate_qrcode(url)
        results = """<img class="qrcode" src="%s" alt="%s" />
                   </br><a href="%s" target="_blank">%s</a>""" % (image, url, url, url)
    else:
        error_msg = _(u"Error Generating QRCODE")
        results = """<div class="alert alert-error">%s</div>""" % error_msg

    return HttpResponse(results, mimetype='text/html')
