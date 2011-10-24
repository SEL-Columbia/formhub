# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django import forms

from pyxform.builder import create_survey_from_xls
from odk_logger.models import XForm
from odk_viewer.models import DataDictionary


class QuickConverter(forms.Form):
    xls_file = forms.FileField(label="XLS File")

    def get_survey(self):
        if self.is_valid():
            xls = self.cleaned_data['xls_file']
            return create_survey_from_xls(xls)


@login_required
def dashboard(request):
    context = RequestContext(request)
    context.form = QuickConverter()
    context.odk_url = request.build_absolute_uri("/%s" % request.user.username)

    if request.method == 'POST':
        form = QuickConverter(request.POST, request.FILES)
        survey = form.get_survey()
        publish(request.user, survey)
        context.message = {
            'type': 'success',
            'text': 'Successfully published %s.' % survey.id_string,
            }
    return render_to_response("dashboard.html", context_instance=context)


def publish(user, survey):
    kwargs = {
        'xml': survey.to_xml(),
        'downloadable': True,
        'user': user,
        }
    xform = XForm.objects.create(**kwargs)

    # need to also make a data dictionary
    kwargs = {
        'xform': xform,
        'json': survey.to_json(),
        }
    data_dictionary = DataDictionary.objects.create(**kwargs)


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
