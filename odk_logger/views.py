#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseBadRequest, \
    HttpResponseRedirect

from models import XForm, create_instance


@require_GET
def formList(request, username):
    """This is where ODK Collect gets its download list."""
    xforms = XForm.objects.filter(downloadable=True, user__username=username)
    urls = [
        {
            'url': request.build_absolute_uri(xform.url()),
            'text': xform.id_string,
            }
        for xform in xforms
        ]
    return render_to_response("formList.xml", {'urls': urls}, mimetype="application/xml")


@require_POST
@csrf_exempt
def submission(request, username):
    # request.FILES is a django.utils.datastructures.MultiValueDict
    # for each key we have a list of values
    xml_file_list = request.FILES.pop("xml_submission_file", [])
    if len(xml_file_list) != 1:
        return HttpResponseBadRequest(
            "There should be a single XML submission file."
            )

    # save this XML file and media files as attachments
    media_files = request.FILES.values()
    create_instance(
        username,
        xml_file_list[0],
        media_files
        )

    # ODK needs two things for a form to be considered successful
    # 1) the status code needs to be 201 (created)
    # 2) The location header needs to be set to the host it posted to
    response = HttpResponse("Your ODK submission was successful.")
    response.status_code = 201
    response['Location'] = request.build_absolute_uri(request.path)
    return response


def download_xform(request, username, id_string):
    xform = XForm.objects.get(user__username=username, id_string=id_string)
    return HttpResponse(
        xform.xml,
        mimetype="application/xml"
        )


def toggle_downloadable(request, username, id_string):
    xform = XForm.objects.get(user__username=username, id_string=id_string)
    xform.downloadable = not xform.downloadable
    xform.save()
    return HttpResponseRedirect("/")


def delete_xform(request, username, id_string):
    xform = XForm.objects.get(user__username=username, id_string=id_string)
    xform.delete()
    return HttpResponseRedirect('/')
