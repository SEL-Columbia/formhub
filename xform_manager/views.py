#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.forms import ModelForm
from django.views.generic.create_update import create_object, update_object
from django.core.urlresolvers import reverse
from django.contrib.auth.models import Group
from django.forms.models import ModelMultipleChoiceField
from django.template import RequestContext

import itertools
from . models import XForm, get_or_create_instance, Instance

@require_GET
def formList(request, group_name):
    """This is where ODK Collect gets its download list."""
    xforms = XForm.objects.filter(downloadable=True) if not group_name \
        else XForm.objects.filter(downloadable=True, groups__name=group_name)
    return render_to_response(
        "formList.xml",
        {"xforms" : xforms, 'root_url': 'http://%s' % request.get_host()},
        mimetype="application/xml"
        )


try:
    from sentry.client.models import client as sentry_client
except:
    # I want to set this code up to not rely on sentry as it breaks
    # testing.
    sentry_client = None
import logging

def log_error(message, level=logging.ERROR):
    if sentry_client is not None:
        sentry_client.create_from_text(message, level=level)
    else:
        print "If sentry was set up we would log the following", \
              message


@require_POST
@csrf_exempt
def submission(request, group_name):
    # request.FILES is a django.utils.datastructures.MultiValueDict
    # for each key we have a list of values
    
    xml_file_list = []
    
    try:
        xml_file_list = request.FILES.pop("xml_submission_file", [])
    except IOError:
#        raise Exception("The connection broke before all files were posted.")
        log_error('The connection broke before all files were posted.')
    if len(xml_file_list)!=1:
        return HttpResponseBadRequest(
            "There should be a single XML submission file."
            )

    # save this XML file and media files as attachments
    media_files = request.FILES.values()
    instance, created = get_or_create_instance(
        xml_file_list[0],
        media_files
        )

    # ODK needs two things for a form to be considered successful
    # 1) the status code needs to be 201 (created)
    # 2) The location header needs to be set to the host it posted to
    response = HttpResponse("Your ODK submission was successful.")
    response.status_code = 201
    response['Location'] = "http://%s/submission" % request.get_host()
    return response

def download_xform(request, id_string, group_name=None):
    xform = XForm.objects.get(id_string=id_string)
    return HttpResponse(
        xform.xml,
        mimetype="application/xml"
        )

def list_xforms(request, group_name=None):
    xforms = XForm.objects.all()
    if group_name:
        # ideally this filtering should be done based on the user's
        # group membership
        xforms = xforms.filter(groups__name=group_name)
    context = RequestContext(request, {"xforms" : xforms})
    return render_to_response(
        "list_xforms.html",
        context_instance=context
        )

def submission_test_form(request):
    """ This view is only for debugging. Do not link to this page. """
    return render_to_response("submission_test_form.html")

# This following code bothers me a little bit, it seems perfectly
# suited to be put in the Django admin.

# CRUD for xforms
# (C)reate using a ModelForm
class CreateXForm(ModelForm):
    class Meta:
        model = XForm
        exclude = ("id_string", "title",)

def create_xform(request, group_name=None):
    return create_object(
        request=request,
        form_class=CreateXForm,
        template_name="form.html",
        post_save_redirect=reverse("list_xforms"),
        )

# (R)ead using a nice list

# (U)pdate using another ModelForm
class UpdateXForm(ModelForm):
    class Meta:
        model = XForm
        fields = ("web_title", "downloadable", "description", "groups",)

def update_xform(request, id_string):
    xform = XForm.objects.get(id_string=id_string)
    return update_object(
        request=request,
        object_id=xform.id,
        form_class=UpdateXForm,
        template_name="form.html",
        post_save_redirect="/", #reverse("list_xforms"),
        )

# (D)elete: we won't let a user actually delete an XForm but they can
# hide XForms using the (U)pdate view
def toggle_downloadable(request, id_string):
    xform = XForm.objects.get(id_string=id_string)
    xform.downloadable = not xform.downloadable
    xform.save()
    return HttpResponseRedirect(reverse("list_xforms"))

def instance(request, pk):
    instance = Instance.objects.get(pk=pk)
    return HttpResponse(instance.as_html())
