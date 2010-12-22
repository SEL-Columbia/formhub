#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response
from djangomako.shortcuts import render_to_response as mako_to_response
from django.http import HttpResponse

from .models import Form, InstanceImage, make_submission

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
    assert len(xml_file_list)==1, \
        "There should be a single xml file in this submission."

    # save the rest of the files to the filesystem
    # these should all be images
    images = []
    for key in request.FILES.keys():
        for image in request.FILES.getlist(key):
            images.append(image)

    make_submission(xml_file_list[0], images)

    # ODK needs two things for a form to be considered successful
    # 1) the status code needs to be 201 (created)
    # 2) The location header needs to be set to the host it posted to
    response = HttpResponse("Your ODK submission was successful.")
    response.status_code = 201
    response['Location'] = "http://%s/submission" % request.get_host()
    return response

def survey_list(request):
    rows = [["Title", "Submission Count", "Last Submission", "Export"]]
    counts = {}
    for form in Form.objects.all():
        if form.title in counts:
            counts[form.title] += 1
        else:
            counts[form.title] = 1
    for form in Form.objects.all():
        rows.append([
                form.title if counts[form.title]==1 else form.id_string,
                form.submission_count(),
                form.date_of_last_submission(),
                '<a href="%s.csv">csv</a>' % form.slug(),
                ])
    return mako_to_response("table2.html", {"rows" : rows})
