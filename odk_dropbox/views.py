#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render_to_response
from djangomako.shortcuts import render_to_response as mako_to_response
from django.http import HttpResponse
import xlwt
import re
from markdown import markdown
import os
import codecs
from . import utils

from .models import Form, Instance, InstanceImage, make_submission

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

read_all_data, created = Permission.objects.get_or_create(
    name = "Can read all data",
    content_type = ContentType.objects.get_for_model(Permission),
    codename = "read_all_data"
    )
@permission_required("auth.read_all_data")
def survey_list(request):
    rows = [["Title", "Submission Count", "Last Submission", "Export"]]
    for form in Form.objects.filter(active=True):
        rows.append([
                form.title,
                Instance.objects.filter(form__title=form.title).count(),
                form.date_of_last_submission(),
                '<a href="/%s.xls">xls</a>' % form.title,
                ])
    return mako_to_response("table2.html", {"rows" : rows})

def xls_to_response(xls, fname):
    response = HttpResponse(mimetype="application/ms-excel")
    response['Content-Disposition'] = 'attachment; filename=%s' % fname
    xls.save(response)
    return response

@permission_required("auth.read_all_data")
def xls(request, title):
    form = Form.objects.get(title=title, active=True)
    form_parser = utils.FormParser(form.path())
    LGA = "lga"
    headers = [LGA]
    for h in form_parser.get_variable_list():
        if not (h.startswith(LGA) or h.startswith("state") or h=="zone"):
            headers.append(h)
    table = [headers]
    for i in Instance.objects.filter(form__title=form.title):
        d = utils.parse_instance(i).get_dict()
        row = []
        for h in headers:
            if h==LGA:
                try:
                    row.append(i.parsedinstance.location.gps.district.name)
                except:
                    found = False
                    for k in d.keys():
                        if k.startswith(LGA):
                            row.append(d[k])
                            found = True
                    if not found: row.append("n/a")
            else: row.append(d.get(h, u"n/a"))
        table.append(row)

    wb = xlwt.Workbook()
    ws = wb.add_sheet("Data")
    for r in range(len(table)):
        for c in range(len(table[r])):
            ws.write(r, c, table[r][c])

    ws = wb.add_sheet("Dictionary")
    parser = utils.FormParser(form.xml_file)
    table = [("Variable Name", "Question Text")]
    table.extend(parser.get_dictionary())
    for r in range(len(table)):
        for c in range(len(table[r])):
            ws.write(r, c, table[r][c])

    return xls_to_response(wb, form.title + ".xls")

def content(request, topic):
    filedir = os.path.dirname(__file__)
    filepath = os.path.join(filedir, "content", topic + ".mkdn")
    f = codecs.open(filepath, mode="r", encoding="utf8")
    text = f.read()
    f.close()
    return HttpResponse(markdown(text))
