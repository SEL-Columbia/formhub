from datetime import datetime
import os
import urllib2

from django import forms
from django.core.urlresolvers import reverse
from django.core.files.storage import default_storage, get_storage_class
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import (HttpResponse, HttpResponseBadRequest,
    HttpResponseRedirect, HttpResponseNotAllowed, Http404,
    HttpResponseForbidden, HttpResponseNotFound, HttpResponseServerError)
from django.shortcuts import render_to_response, get_object_or_404
from django.template import loader, RequestContext
from django.utils import simplejson
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_GET, require_POST
from google_doc import GoogleDoc
from guardian.shortcuts import assign, remove_perm, get_users_with_perms

from main.forms import UserProfileForm, FormLicenseForm, DataLicenseForm,\
    SupportDocForm, QuickConverterFile, QuickConverterURL, QuickConverter,\
    SourceForm, PermissionForm, MediaForm, MapboxLayerForm
from main.models import UserProfile, MetaData
from odk_logger.models import Instance, XForm
from odk_viewer.models import DataDictionary, ParsedInstance
from odk_viewer.models.data_dictionary import upload_to
from odk_viewer.views import image_urls_for_form, survey_responses
from utils.decorators import is_owner
from utils.logger_tools import response_with_mimetype_and_name, publish_form
from utils.user_auth import check_and_set_user, set_profile_data,\
    has_permission, helper_auth_helper, get_xform_and_perms,\
    check_and_set_user_and_form


def home(request):
    context = RequestContext(request)
    context.num_forms = Instance.objects.count()
    context.num_users = User.objects.count()
    context.num_shared_forms = XForm.objects.filter(shared__exact=1).count()
    if request.user.username:
        return HttpResponseRedirect(
            reverse(profile, kwargs={'username': request.user.username}))
    else:
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
            return {
                'type': 'alert-success',
                'text': _(u'Successfully cloned %(id_string)s into your '
                          u'%(profile_url)s') % {
                              'id_string': survey.id_string,
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
    content_user = None
    context.num_surveys = Instance.objects.count()
    context.form = QuickConverter()

    # xlsform submission...
    if request.method == 'POST' and request.user.is_authenticated():
        def set_form():
            form = QuickConverter(request.POST, request.FILES)
            survey = form.publish(request.user).survey
            return {
                'type': 'alert-success',
                'text': _(u'Successfully published %s.') % survey.id_string
            }
        context.message = publish_form(set_form)

    # profile view...
    content_user = get_object_or_404(User, username=username)
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
    # for any other user -> profile
    profile, created = UserProfile.objects.get_or_create(user=content_user)
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
            return HttpResponseRedirect(reverse(
                public_profile, kwargs={'username': request.user.username}
            ))
    else:
        form = UserProfileForm(instance=profile,initial= {"email": content_user.email})
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
    Returns public infomation about the forn as JSON
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
            xform.description = request.POST['description']
        elif request.POST.get('title'):
            xform.title = request.POST['title']
        elif request.POST.get('toggle_shared'):
            if request.POST['toggle_shared'] == 'data':
                xform.shared_data = not xform.shared_data
            elif request.POST['toggle_shared'] == 'form':
                xform.shared = not xform.shared
            elif request.POST['toggle_shared'] == 'active':
                xform.downloadable = not xform.downloadable
            elif request.POST['toggle_shared'] == 'crowd':
                if xform.is_crowd_form:
                    xform.is_crowd_form = False
                else:
                    xform.is_crowd_form = True
                    xform.shared = True
                    xform.shared_data = True
        elif request.POST.get('form-license'):
            MetaData.form_license(xform, request.POST['form-license'])
        elif request.POST.get('data-license'):
            MetaData.data_license(xform, request.POST['data-license'])
        elif request.POST.get('source') or request.FILES.get('source'):
            MetaData.source(xform, request.POST.get('source'),
                            request.FILES.get('source'))
        elif request.FILES.get('media'):
            MetaData.media_upload(xform, request.FILES.get('media'))
        elif request.POST.get('map_name'):
            mapbox_layer = MapboxLayerForm(request.POST)
            if mapbox_layer.is_valid():
                MetaData.mapbox_layer_upload(xform, mapbox_layer.cleaned_data)
        elif request.FILES:
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


def support(request):
    context = RequestContext(request)
    context.template = 'support.html'
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


def syntax(request):
    url = 'https://docs.google.com/document/pub?id=1Dze4IZGr0IoIFuFAI_ohKR5mY'\
        'Ut4IAn5Y-uCJmnv1FQ'
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
    if username == request.user.username or xform.shared:
        data = get_object_or_404(MetaData, pk=data_id)
        file_path = data.data_file.name
        filename, extension = os.path.splitext(file_path.split('/')[-1])
        extension = extension.strip('.')
        default_storage = get_storage_class()()
        if default_storage.exists(file_path):
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
    data = get_object_or_404(MetaData, pk=data_id)
    default_storage = get_storage_class()()
    if request.GET.get('del', False) and username == request.user.username:
        try:
            default_storage.delete(data.data_file.name)
            data.delete()
            return HttpResponseRedirect(reverse(show, kwargs={
                'username': username,
                'id_string': id_string
            }))
        except Exception, e:
            return HttpResponseServerError()
    elif request.GET.get('map_name_del', False) and\
         username == request.user.username:
        data.delete()
        return HttpResponseRedirect(reverse(show, kwargs={
            'username': username,
            'id_string': id_string
        }))
    return HttpResponseForbidden(_(u'Permission denied.'))


def download_media_data(request, username, id_string, data_id):
    data = get_object_or_404(MetaData, id=data_id)
    default_storage = get_storage_class()()
    if request.GET.get('del', False):
        if username == request.user.username:
            try:
                default_storage.delete(data.data_file.name)
                data.delete()
                return HttpResponseRedirect(reverse(show, kwargs={
                    'username': username,
                    'id_string': id_string
                }))
            except Exception, e:
                return HttpResponseServerError()
    else:
        xform = get_object_or_404(XForm,
                                  user__username=username, id_string=id_string)
        if username: # == request.user.username or xform.shared:
            file_path = data.data_file.name
            filename, extension = os.path.splitext(file_path.split('/')[-1])
            extension = extension.strip('.')
            if default_storage.exists(file_path):
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
    context.images = image_urls_for_form(xform)
    context.profile, created = UserProfile.objects.get_or_create(user=owner)
    return render_to_response('form_photos.html', context_instance=context)


@require_POST
@is_owner
def set_perm(request, username, id_string):
    xform = get_object_or_404(XForm,
                              user__username=username, id_string=id_string)
    try:
        perm_type = request.POST['perm_type']
        for_user = request.POST['for_user']
    except KeyError:
        return HttpResponseBadRequest()
    if perm_type in ['edit', 'view', 'remove']:
        user = User.objects.get(username=for_user)
        if perm_type == 'edit':
            assign('change_xform', user, xform)
        elif perm_type == 'view':
            assign('view_xform', user, xform)
        elif perm_type == 'remove':
            remove_perm('change_xform', user, xform)
            remove_perm('view_xform', user, xform)
    elif perm_type == 'link':
        if for_user == 'all':
            MetaData.public_link(xform, True)
        elif for_user == 'none':
            MetaData.public_link(xform, False)
        elif for_user == 'toggle':
            current = MetaData.public_link(xform)
            MetaData.public_link(xform, not current)
    return HttpResponseRedirect(reverse(show, kwargs={
        'username': username,
        'id_string': id_string
    }))


def show_submission(request, username, id_string, uuid):
    xform, is_owner, can_edit, can_view = get_xform_and_perms(
        username, id_string, request)
    # no access
    if not (xform.shared_data or can_view or
            request.session.get('public_link')):
        return HttpResponseRedirect(reverse(home))
    submission = get_object_or_404(Instance, uuid=uuid)
    return HttpResponseRedirect(reverse(
        survey_responses, kwargs={'instance_id': submission.pk}))


@require_GET
def delete_data(request, username=None, id_string=None):
    xform, owner = check_and_set_user_and_form(username, id_string, request)
    if not xform:
        return HttpResponseForbidden(_(u'Not shared.'))
    try:
        args = {"username": username, "id_string": id_string,
                "query": request.GET.get('query'),
                "fields": request.GET.get('fields'),
                "sort": request.GET.get('sort')}

        if 'limit' in request.GET:
            args["limit"] = int(request.GET.get('limit'))
        cursor = ParsedInstance.query_mongo(**args)
    except ValueError as e:
        return HttpResponseBadRequest(e)

    today = datetime.today().strftime('%Y-%m-%dT%H:%M:%S')
    ParsedInstance.edit_mongo(
        args['query'], '{ "$set": {"_deleted_at": "%s" }}' % today)

    records = list(record for record in cursor)
    response_text = simplejson.dumps(records)
    if 'callback' in request.GET and request.GET.get('callback') != '':
        callback = request.GET.get('callback')
        response_text = ("%s(%s)" % (callback, response_text))
    return HttpResponse(response_text, mimetype='application/json')


@require_POST
@is_owner
def link_to_bamboo(request, username, id_string):
    xform = get_object_or_404(XForm,
                              user__username=username, id_string=id_string)
    
    from utils.bamboo import get_new_bamboo_dataset
    dataset_id = get_new_bamboo_dataset(xform)
    xform.bamboo_dataset = dataset_id
    xform.save()

    return HttpResponseRedirect(reverse(show, kwargs={
        'username': username,
        'id_string': id_string
    }))
