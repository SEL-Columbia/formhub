import os, urllib2

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.core.files.storage import default_storage
from django.template import RequestContext
from django import forms
from django.db import IntegrityError
from django.contrib.auth.models import User
from django.views.decorators.http import require_GET, require_POST
from django.http import HttpResponse, HttpResponseBadRequest, \
    HttpResponseRedirect, HttpResponseNotAllowed, HttpResponseForbidden
from django.utils import simplejson
from django.shortcuts import render_to_response, get_object_or_404
from pyxform.errors import PyXFormError
from guardian.shortcuts import assign, remove_perm, get_users_with_perms

from main.models import UserProfile, MetaData
from main.forms import UserProfileForm, FormLicenseForm, DataLicenseForm,\
         SupportDocForm, QuickConverterFile, QuickConverterURL, QuickConverter,\
     SourceForm, PermissionForm
from odk_logger.models import Instance, XForm
from odk_logger.models.xform import XLSFormError
from odk_viewer.models import DataDictionary
from odk_viewer.models.data_dictionary import upload_to
from odk_viewer.views import image_urls_for_form, survey_responses
from utils.logger_tools import response_with_mimetype_and_name
from utils.decorators import is_owner
from utils.user_auth import check_and_set_user, set_profile_data,\
         has_permission, get_xform_and_perms

def home(request):
    context = RequestContext(request)
    context.num_forms = Instance.objects.count()
    context.num_users = User.objects.count()
    context.num_shared_forms = XForm.objects.filter(shared__exact=1).count()
    if request.user.username:
        return HttpResponseRedirect(reverse(profile,
            kwargs={'username': request.user.username}))
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

    try:
        form_owner = request.POST.get('username')
        id_string = request.POST.get('id_string')
        xform = XForm.objects.get(user__username=form_owner, \
                                    id_string=id_string)
        if len(id_string) > 0 and id_string[0].isdigit():
            id_string = '_' + id_string
        path = xform.xls.name
        if default_storage.exists(path):
            xls_file = upload_to(None, id_string + '_cloned.xls', to_username)
            xls_data = default_storage.open(path)
            xls_file = default_storage.save(xls_file, xls_data)
            context.message = u"%s-%s" % (form_owner, xls_file)
            survey = DataDictionary.objects.create(
                user=request.user,
                xls=xls_file
                ).survey
            context.message = {
                'type': 'success',
                'text': 'Successfully cloned %s into your '\
                        '<a href="%s">profile</a>.' % \
                        (survey.id_string, reverse(profile,
                            kwargs={'username': to_username}))
                }
    except (PyXFormError, XLSFormError) as e:
        context.message = {
            'type': 'error',
            'text': unicode(e),
            }
    except IntegrityError as e:
        context.message = {
            'type': 'error',
            'text': 'Form with this id already exists.',
            }
    if request.is_ajax():
        return HttpResponse(simplejson.dumps(context.message), \
                        mimetype='application/json')
    else:
        return HttpResponse(context.message['text'])


def profile(request, username):
    context = RequestContext(request)
    content_user = None
    context.num_surveys = Instance.objects.count()
    context.form = QuickConverter()

    # xlsform submission...
    if request.method == 'POST' and request.user.is_authenticated():
        try:
            form = QuickConverter(request.POST, request.FILES)
            survey = form.publish(request.user).survey
            context.message = {
                'type': 'success',
                'text': 'Successfully published %s.' % survey.id_string,
                }
        except (PyXFormError, XLSFormError) as e:
            context.message = {
                'type': 'error',
                'text': unicode(e),
                }
        except IntegrityError as e:
            context.message = {
                'type': 'error',
                'text': 'Form with this id already exists.',
                }

    # profile view...
    content_user = get_object_or_404(User, username=username)
    # for the same user -> dashboard
    if content_user == request.user:
        context.show_dashboard = True
        context.user_surveys = content_user.surveys.count()
        context.all_forms = content_user.xforms.count()
        context.form = QuickConverterFile()
        context.form_url = QuickConverterURL()
        context.odk_url = request.build_absolute_uri("/%s" % request.user.username)
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
            form.save()
            return HttpResponseRedirect(reverse(public_profile,
                kwargs={'username': request.user.username}))
    else:
        form = UserProfileForm(instance=profile)
    return render_to_response("settings.html", { 'form': form },
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
    xform, is_owner, can_edit, can_view = get_xform_and_perms(username,\
            id_string, request)
    # no access
    if not (xform.shared or can_view or request.session.get('public_link')):
        return HttpResponseRedirect(reverse(home))
    context = RequestContext(request)
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
    if is_owner:
        context.form_license_form = FormLicenseForm(
                initial={'value': context.form_license})
        context.data_license_form = DataLicenseForm(
                initial={'value': context.data_license})
        context.doc_form = SupportDocForm()
        context.source_form = SourceForm()
        context.users_with_perms = get_users_with_perms(xform,
                attach_perms=True).items()
        context.permission_form = PermissionForm(username)
    return render_to_response("show.html", context_instance=context)


@require_POST
@login_required
def edit(request, username, id_string):
    xform = XForm.objects.get(user__username=username, id_string=id_string)
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
        elif request.POST.get('form-license'):
            MetaData.form_license(xform, request.POST['form-license'])
        elif request.POST.get('data-license'):
            MetaData.data_license(xform, request.POST['data-license'])
        elif request.POST.get('source') or request.FILES.get('source'):
            MetaData.source(xform, request.POST.get('source'),
                request.FILES.get('source'))
        elif request.FILES:
            MetaData.supporting_docs(xform, request.FILES['doc'])
        xform.update()
        if request.is_ajax():
            return HttpResponse('Updated succeeded.')
        else:
            return HttpResponseRedirect(reverse(show, kwargs={
                        'username': username,
                        'id_string': id_string
                        }))
    return HttpResponseForbidden('Update failed.')


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


from google_doc import GoogleDoc


def syntax(request):
    url = 'https://docs.google.com/document/pub?id=1Dze4IZGr0IoIFuFAI_ohKR5mYUt4IAn5Y-uCJmnv1FQ'
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
    context.shared_forms = DataDictionary.objects.filter(shared=True)
    return render_to_response('form_gallery.html', context_instance=context)

def download_metadata(request, username, id_string, data_id):
    xform = get_object_or_404(XForm,
            user__username=username, id_string=id_string)
    if username == request.user.username or xform.shared:
        data = MetaData.objects.get(pk=data_id)
        return response_with_mimetype_and_name(
            data.data_file_type,
            data.data_value, '', None, False,
            data.data_file.name)
    return HttpResponseForbidden('Permission denied.')

def form_photos(request, username, id_string):
    xform = get_object_or_404(XForm,
            user__username=username, id_string=id_string)
    owner = User.objects.get(username=username)
    if not has_permission(xform, owner, request):
        return HttpResponseForbidden('Not shared.')
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
    xform, is_owner, can_edit, can_view = get_xform_and_perms(username,\
            id_string, request)
    # no access
    if not (xform.shared_data or can_view or
            request.session.get('public_link')):
        return HttpResponseRedirect(reverse(home))
    submission = get_object_or_404(Instance, uuid=uuid)
    return HttpResponseRedirect(reverse(survey_responses,
                kwargs={ 'instance_id': submission.pk }))
