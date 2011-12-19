import os

from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django import forms
from django.db import IntegrityError

from pyxform.errors import PyXFormError
from odk_viewer.models import DataDictionary
from utils.quick_converter import QuickConverter
from utils.google_doc import GoogleDoc

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


def public_profile(request):
    context = RequestContext(request)
    context.form = QuickConverter()
    context.odk_url = request.build_absolute_uri("/%s" % request.user.username)

    return render_to_response("public_profile.html", context_instance=context)


def tutorial(request):
    context = RequestContext(request)
    context.template = 'tutorial.html'
    username = request.user.username if request.user.username else \
        'your-user-name'
    context.odk_url = request.build_absolute_uri("/%s" % username)
    return render_to_response('base.html', context_instance=context)

def support(request):
    context = RequestContext(request)
    context.template = 'support.html'
    return render_to_response('base.html', context_instance=context)

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
