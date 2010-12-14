#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import os, glob
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response
from django.http import HttpResponse

from .models import Form, Submission, SubmissionImage

@require_GET
def formList(request):
    forms = [(f.name(), f.url()) for f in Form.objects.filter(active=True)]
    return render_to_response("formList.xml",
                              {"forms": forms},
                              mimetype="application/xml")

@require_POST
@csrf_exempt
def submission(request):
    # request.FILES is a django.utils.datastructures.MultiValueDict
    # for each key we have a list of values
    xml_file_list = request.FILES.pop("xml_submission_file")
    assert len(xml_file_list)==1, "There should be a single xml file in this submission."
    s = Submission(xml_file=xml_file_list[0])
    s.save()

    # save the rest of the files to the filesystem
    # these should all be images
    for key in request.FILES.keys():
        for image in request.FILES.getlist(key):
            SubmissionImage.objects.create(submission=s, image=image)

    # ODK needs two things for a form to be considered successful
    # 1) the status code needs to be 201 (created)
    # 2) The location header needs to be set to the host it posted to
    response = HttpResponse("You've successfully made an odk submission.")
    response.status_code = 201
    response['Location'] = "http://%s/submission" % request.get_host()
    return response

def import_instances_folder(path):
    for instance in glob.glob( os.path.join(path, "*") ):
        xml_files = glob.glob( os.path.join(instance, "*.xml") )
        if len(xml_files)!=1: continue
        print xml_files[0]
        f = django_file(xml_files[0], field_name="xml_file", content_type="text/xml")
        s = Submission(xml_file=f)
        s.save()

        for jpg in glob.glob( os.path.join(instance, "*.jpg") ):
            print jpg
            f = django_file(jpg, field_name="image", content_type="image/jpeg")
            SubmissionImage.objects.create(submission=s, image=f)

def django_file(path, field_name, content_type):
    # adapted from here: http://groups.google.com/group/django-users/browse_thread/thread/834f988876ff3c45/
    from django.core.files.uploadedfile import InMemoryUploadedFile
    f = open(path)
    return InMemoryUploadedFile(
        file=f,
        field_name=field_name,
        name=f.name,
        content_type=content_type,
        size=os.path.getsize(path),
        charset=None)
