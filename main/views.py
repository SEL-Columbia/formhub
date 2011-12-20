# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import os

from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django import forms
from django.db import IntegrityError
from django.contrib.auth.models import User
from django.views.decorators.http import require_GET
from django.http import HttpResponse, HttpResponseBadRequest, \
    HttpResponseRedirect

from pyxform.errors import PyXFormError
from odk_viewer.models import DataDictionary
from gravatar import get_gravatar_img_link


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
    context.form = QuickConverter()

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
    return render_to_response("home.html", context_instance=context)


@login_required
def login_redirect(request):
    return HttpResponseRedirect("/%s" % request.user.username)


@require_GET
def profile(request, username):
    context = RequestContext(request)
    content_user = None
    try:
        content_user = User.objects.get(username=username)
    except User.DoesNotExist:
        return HttpResponseRedirect("/")
    if content_user == request.user:
        context.show_dashboard = True
    context.content_user = content_user
    context.content_user_gravatar_img_link = get_gravatar_img_link(content_user)
    return render_to_response("profile.html", context_instance=context)


@require_GET
@login_required
def public_profile(request, username):
    if username != request.user.username:
        return HttpResponseRedirect("/%s" % username)
    context = RequestContext(request)
    content_user = None
    try:
        content_user = User.objects.get(username=username)
    except User.DoesNotExist:
        return HttpResponseRedirect("/")
    context.content_user = content_user
    context.content_user_gravatar_img_link = get_gravatar_img_link(content_user)
    return render_to_response("profile.html", context_instance=context)


@login_required
def dashboard(request):
    context = RequestContext(request)
    context.form = QuickConverter()
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


def gallery(request):
    """
    Return a list of urls for all the shared xls files. This could be
    made a lot prettier.
    """
    context = RequestContext(request)
    context.shared_forms = DataDictionary.objects.filter(shared=True)
    return render_to_response('gallery.html', context_instance=context)
