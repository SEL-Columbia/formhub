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
        xls = self.cleaned_data['xls_file']
        survey = create_survey_from_xls(xls)
        return survey


@login_required
def dashboard(request):
    if request.method == 'POST':
        form = QuickConverter(request.POST, request.FILES)
        if form.is_valid():
            survey = form.get_survey()
            publish(request.user, survey)
            form = QuickConverter()
    else:
        form = QuickConverter()

    context = RequestContext(request)
    context.form = form
    return render_to_response("dashboard.html", context_instance=context)


def publish(user, survey):
    kwargs = {
        'xml': survey.to_xml(),
        'downloadable': True,
        'user': user,
        }
    xform, created = XForm.objects.get_or_create(**kwargs)

    # need to also make a data dictionary
    kwargs = {
        'xform': xform,
        'json': survey.to_json(),
        }
    data_dictionary, created = DataDictionary.objects.get_or_create(**kwargs)


def tutorial(request):
    return render_to_response('tutorial_wrap.html')
