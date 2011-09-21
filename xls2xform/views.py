import json
import os
import re

from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from models import Survey
from pyxform.xls2json import SurveyReader
from pyxform.builder import create_survey_from_xls

from xls2xform.utils import slugify
from xls2xform.exporter import export_survey


class QuickConverter(forms.Form):
    xls_file = forms.FileField(label="XLS File")

    def get_survey(self):
        xls = self.cleaned_data['xls_file']
        survey = create_survey_from_xls(xls)
        return survey


class CreateSurvey(forms.Form):
    title = forms.CharField()
    root_name = forms.CharField(label="ID String")

    def clean_root_name(self):
        root_name = slugify(self.data.get(u'root_name'))
        user = self.data.get(u'user')
        existing_forms = Survey.objects.filter(root_name=root_name,
                     user=user).count()
        if existing_forms > 0:
            raise forms.ValidationError("You already have a form with this ID string: %s" % root_name)
        return root_name


# this is probably replaced by main.views.index
def home(request, **kwargs):
    context = RequestContext(request)
    context.title = "XLS2Survey v2.0-beta1"
    context.form = CreateSurvey()
    context.page_name = "Home"
    context.update(kwargs)

    if request.method == "POST":
        root_name = request.POST.get(u'root_name')
        title = request.POST.get(u'title')

        submitted_form = CreateSurvey({
            'root_name': root_name,
            'title': title,
            'user': request.user
        })
        if submitted_form.is_valid():
            xf_data = submitted_form.cleaned_data
            xf_data['user'] = request.user
            xf = Survey.objects.create(**xf_data)
            edit_url = reverse(edit_survey, kwargs={'survey_root_name': xf.root_name})
            return HttpResponseRedirect(edit_url)
        else:
            #passed back to the page to display errors.
            context.form = submitted_form
    context.surveys = request.user.surveys.all()
    return render_to_response("xls2xform.html", context_instance=context)



def delete_survey(request, survey_root_name):
    survey = request.user.surveys.get(root_name=survey_root_name)
    survey.delete()
    return HttpResponseRedirect(reverse(home))


def download_survey(request, survey_root_name, format):
    # TODO:
    # GET XFORM EXPORT WORKING WITH PYXFORM!!
    # currently spitting out JSON
    format = "json"
    survey = request.user.surveys.get(root_name=survey_root_name)
    import simplejson as json
    xf_filename = "SAMPLE_%s.json" % survey_root_name
    response = HttpResponse(json.dumps(survey._survey_package(), indent=4), mimetype="application/download")
    response['Content-Disposition'] = 'attachment; filename=%s' % xf_filename
    return response

    # This used to work, but I put the stuff above to debug.
    survey = request.user.surveys.get(root_name=survey_root_name)
    survey_object = export_survey(survey)
    xf_filename = "%s.%s" % (survey_object.root_name(), format)
    if format == 'xml':
        survey_str = survey_object.to_xml()
    elif format == 'json':
        survey_str = json.dumps(survey_object.to_dict(), indent=4)
    else:
        raise Exception("Unknown file format", format)
    response = HttpResponse(survey_str, mimetype="application/download")
    response['Content-Disposition'] = 'attachment; filename=%s' % xf_filename
    return response


def convert_file_to_children_json(file_io):
    file_name = file_io.name
    if re.search("\.json$", file_name):
        slug = re.sub(".json$", "", file_name)
        # Loading json io into json lets us ensure
        # that the json is valid.
        children_list = json.loads(file_io.read())
        if type(children_list) == dict:
            children_list = children_list[u'children']
        children_json = json.dumps(children_list)
    elif re.search("\.xls$", file_name) or re.search("\.csv$", file_name):
        slug, children_json = process_spreadsheet_io_to_children_json(file_io)
    else:
        raise Exception("This file is not understood: %s" % file_name)
    return (slug, children_json)


def save_in_temp_dir(file_io):
    file_name = file_io.name
    tmp_xls_dir = os.path.join(settings.PROJECT_ROOT, "xls_tmp")
    if not os.path.exists(tmp_xls_dir):
        os.mkdir(tmp_xls_dir)
    path = os.path.join(tmp_xls_dir, file_name)
    with open(path, 'w') as f:
        f.write(file_io.read())
    return path


def process_spreadsheet_io_to_children_json(file_io):
    # I agree that this function is not pretty, but I don't think we
    # should move this into the model because I prefer to think of the
    # model as file-format independent.
    path = save_in_temp_dir(file_io)
    directory, filename = os.path.split(path)
    slug, extension = os.path.splitext(filename)
    xlr = SurveyReader(path)
    xls_vals = xlr.to_dict()[u'children']
    qjson = json.dumps(xls_vals)
    os.remove(path)
    return (slug, qjson)


@login_required
def edit_survey(request, survey_root_name):
    context = RequestContext(request)
    surveys = request.user.surveys
    survey = surveys.get(root_name=survey_root_name)
    context.page_name = "Edit - %s" % survey.title
    context.title = "Edit Survey - %s" % survey.title
    if u'section_file' in request.FILES:
        # a file has been posted
        section_file = request.FILES[u'section_file']
        slug, children_json = convert_file_to_children_json(section_file)
        survey.add_or_update_section(slug=slug, children_json=children_json)
    context.survey = survey
    #section_portfolio:
    # --> all sections that have been uploaded to this form
    #included_base_sections:
    # --> all sections that have been specified for use in the base_section
    context.section = survey.base_section
    surveys_available_sections = [s for s in survey.survey_sections.order_by('slug').all()
                                        if s.slug != '_base']
    context.available_sections = surveys_available_sections
    bsids = survey._base_section.includes_list
    context.base_sections = [survey.survey_sections.get(slug=bs)
                                for bs in bsids]
    return render_to_response("edit_xform.html", context_instance=context)

@login_required
def edit_section(request, survey_root_name, section_slug, action):
    user = request.user
    survey = user.surveys.get(root_name=survey_root_name)
    section = survey.survey_sections.get(slug=section_slug)
    section.make_adjustment(survey.base_section, action)
    return HttpResponseRedirect(
        reverse(edit_survey, kwargs={'survey_root_name': survey.root_name})
        )
