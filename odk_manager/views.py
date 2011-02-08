#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseBadRequest
from django.forms import ModelForm
from django.views.generic.create_update import create_object, update_object
from django.core.urlresolvers import reverse

import itertools
from . models import XForm, get_or_create_instance

@require_GET
def formList(request):
    """This is where ODK Collect gets its download list."""
    forms = [f.id_string for f in XForm.objects.filter(downloadable=True)]
    return render_to_response("formList.xml",
                              {"forms": forms},
                              mimetype="application/xml")

@require_POST
@csrf_exempt
def submission(request):
    # request.FILES is a django.utils.datastructures.MultiValueDict
    # for each key we have a list of values
    try:
        xml_file_list = request.FILES.pop("xml_submission_file", [])

        # save this XML file and media files as attachments
        instance, created = get_or_create_instance(
            xml_file_list[0],
            list(itertools.chain(*request.FILES.values()))
            )

        # ODK needs two things for a form to be considered successful
        # 1) the status code needs to be 201 (created)
        # 2) The location header needs to be set to the host it posted to
        response = HttpResponse("Your ODK submission was successful.")
        response.status_code = 201
        response['Location'] = "http://%s/submission" % request.get_host()
        return response
    except:
        # catch any exceptions and print them to the error log
        # it'd be good to add more info to these error logs
        return HttpResponseBadRequest(
            "We need to improve our error messages and logging."
            )

# This following code bothers me a little bit, it seems perfectly
# suited to be put in the Django admin.

# CRUD for xforms
# (C)reate using a ModelForm
class CreateXForm(ModelForm):
    class Meta:
        model = XForm
        exclude = ("id_string", "title",)

def create_xform(request):
    return create_object(
        request=request,
        form_class=CreateXForm,
        template_name="form.html",
        post_save_redirect=reverse("list-xforms"),
        )

# (R)ead using a nice list
def list_xforms(request):
    return render_to_response(
        "list_xforms.html",
        {"xforms" : XForm.objects.all()}
        )

# (U)pdate using another ModelForm
class UpdateXForm(ModelForm):
    class Meta:
        model = XForm
        fields = ("web_title", "downloadable", "description",)

def update_xform(request, pk):
    return update_object(
        request=request,
        object_id=pk,
        form_class=UpdateXForm,
        template_name="form.html",
        post_save_redirect=reverse("list-xforms"),
        )

# (D)elete: we won't let a user actually delete an XForm but they can
# hide XForms using the (U)pdate view
