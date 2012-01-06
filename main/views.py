import os

from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django import forms
from django.db import IntegrityError
from django.contrib.auth.models import User
from django.views.decorators.http import require_GET, require_POST
from django.http import HttpResponse, HttpResponseBadRequest, \
    HttpResponseRedirect, HttpResponseNotAllowed

from pyxform.errors import PyXFormError
from odk_viewer.models import DataDictionary
from main.models import UserProfile
from odk_logger.models import Instance, XForm
from utils.user_auth import check_and_set_user, set_profile_data
from main.forms import UserProfileForm

class QuickConverter(forms.Form):
    xls_file = forms.FileField(label="XLS File")

    def publish(self, user):
        if self.is_valid():
            return DataDictionary.objects.create(
                user=user,
                xls=self.cleaned_data['xls_file']
                )


def home(request):
    context = RequestContext(request)
    context.num_forms = Instance.objects.count()
    context.num_users = User.objects.count()
    return render_to_response("home.html", context_instance=context)


@login_required
def login_redirect(request):
    return HttpResponseRedirect("/%s" % request.user.username)


def profile(request, username):
    context = RequestContext(request)
    content_user = None
    context.num_surveys = Instance.objects.count()
    context.form = QuickConverter()

    # xlsform submission...
    if request.method == 'POST':
        try:
            form = QuickConverter(request.POST, request.FILES)
            survey = form.publish(request.user).survey
            context.message = {
                'type': 'success',
                'text': 'Successfully published %s.' % survey.id_string,
                }
        except PyXFormError as e:
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
    try:
        content_user = User.objects.get(username=username)
    except User.DoesNotExist:
        return HttpResponseRedirect("/")
    # for the same user -> dashboard
    if content_user == request.user:
        context.show_dashboard = True
        context.form = QuickConverter()
        context.odk_url = request.build_absolute_uri("/%s" % request.user.username)
    # for any other user -> profile
    profile, created = UserProfile.objects.get_or_create(user=content_user)
    set_profile_data(context, content_user)
    return render_to_response("profile.html", context_instance=context)


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
            return HttpResponseRedirect("/%s/profile" % content_user.username)
    else:
        form = UserProfileForm(instance=profile)
    return render_to_response("settings.html", { 'form': form }, context_instance=context)


@require_GET
def public_profile(request, username):
    content_user = check_and_set_user(request, username)
    if isinstance(content_user, HttpResponseRedirect):
        return content_user
    context = RequestContext(request)
    set_profile_data(context, content_user)
    return render_to_response("profile.html", context_instance=context)


@login_required
def dashboard(request):
    context = RequestContext(request)
    context.form = QuickConverter()
    content_user = request.user
    set_profile_data(context, content_user)
    context.odk_url = request.build_absolute_uri("/%s" % request.user.username)

    if request.method == 'POST':
        try:
            form = QuickConverter(request.POST, request.FILES)
            survey = form.publish(request.user).survey
            context.message = {
                'type': 'success',
                'text': 'Successfully published %s.' % survey.id_string,
                }
        except PyXFormError as e:
            context.message = {
                'type': 'error',
                'text': unicode(e),
                }
        except IntegrityError as e:
            context.message = {
                'type': 'error',
                'text': 'Form with this id already exists.',
                }
    return render_to_response("dashboard.html", context_instance=context)


@require_GET
def show(request, username, id_string):
    xform = XForm.objects.get(user__username=username, id_string=id_string)
    is_owner = username == request.user.username
    # no access
    if xform.shared == False and not is_owner:
        return HttpResponseRedirect("/")
    context = RequestContext(request)
    context.is_owner = is_owner
    context.xform = xform
    context.content_user = xform.user
    return render_to_response("show.html", context_instance=context)

@require_POST
@login_required
def edit(request, username, id_string):
    if username == request.user.username:
        xform = XForm.objects.get(user__username=username, id_string=id_string)
        if request.POST.get('description'):
            xform.description = request.POST['description']
        if request.POST.get('toggle_data_download'):
            raise Exception(xform.downloadable)
            xform.downloadable = not xform.downloadable
        xform.save()
        return HttpResponse('Updated succeeded.')
    return HttpResponseNotAllowed('Update failed.')

def support(request):
    context = RequestContext(request)
    context.template = 'support.html'
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
    context.shared_forms = DataDictionary.objects.filter(shared=True)
    return render_to_response('form_gallery.html', context_instance=context)
