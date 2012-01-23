from django.core.servers.basehttp import FileWrapper
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseBadRequest, \
    HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.contrib.auth.models import User
from django.contrib import messages
from models import XForm, create_instance
from utils import response_with_mimetype_and_name
from odk_logger.import_tools import import_instances_from_zip
import zipfile
import tempfile
import os


@require_POST
@csrf_exempt
def bulksubmission(request, username):
    # puts it in a temp directory.
    # runs "import_tools(temp_directory)"
    # deletes
    try:
        posting_user = User.objects.get(username=username)
    except User.DoesNotExist:
        return HttpResponseBadRequest("User %s not found" % username)

    # request.FILES is a django.utils.datastructures.MultiValueDict
    # for each key we have a list of values
    temp_postfile = request.FILES.pop("zip_submission_file", [])
    if len(temp_postfile) == 1:
        postfile = temp_postfile[0]
        tempdir = tempfile.gettempdir()
        our_tfpath = os.path.join(tempdir, postfile.name)
        our_tempfile = open(our_tfpath, 'wb')
        our_tempfile.write(postfile.read())
        our_tempfile.close()
        our_tf = open(our_tfpath, 'rb')
        count = import_instances_from_zip(our_tf, user=posting_user)
        os.remove(our_tfpath)
        response = HttpResponse("Your ODK submission was successful. %d surveys imported. Your user now has %d instances." % \
                    (count, posting_user.surveys.count()))
        response.status_code = 200
        response['Location'] = request.build_absolute_uri(request.path)
        return response
    else:
        return HttpResponseBadRequest("There was a problem receiving your ODK submission. [Error: multiple submission files (?)]")


def bulksubmission_form(request, username=None):
	return render_to_response("bulk_submission_form.html")


@require_GET
def formList(request, username):
    """This is where ODK Collect gets its download list."""
    xforms = XForm.objects.filter(downloadable=True, user__username=username)
    urls = [
        {
            'url': request.build_absolute_uri(xform.url()),
            'text': xform.title,
        }
        for xform in xforms
        ]
    return render_to_response("formList.xml", {'urls': urls}, mimetype="text/xml")


@require_POST
@csrf_exempt
def submission(request, username):
    # request.FILES is a django.utils.datastructures.MultiValueDict
    # for each key we have a list of values
    try:
        xml_file_list = request.FILES.pop("xml_submission_file", [])
    except IOError, v:
        try:
            (code, message) = v
        except:
            code = 0
            message = v
        if message == 'request data read error':
            return HttpResponseBadRequest("File transfer interruption.")
        else:
            raise
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
    response = response_with_mimetype_and_name('xml', id_string, show_date=False)
    response.content = xform.xml
    return response

def download_xlsform(request, username, id_string):
    xform = XForm.objects.get(user__username=username, id_string=id_string)
    path = os.path.join('media', xform.xls.path)
    if os.path.exists(path):
        response = response_with_mimetype_and_name('vnd.ms-excel', id_string, show_date=False,
                extension='xls', file_path=path)
        return response
    else:
        messages.add_message(request, messages.WARNING, 'No XLS file for your form <strong>%s</strong>' % id_string)
        return HttpResponseRedirect("/%s" % username)

def download_jsonform(request, username, id_string):
    xform = XForm.objects.get(user__username=username, id_string=id_string)
    response = response_with_mimetype_and_name('json', id_string, show_date=False)
    response.content = xform.json
    return response

def delete_xform(request, username, id_string):
    xform = XForm.objects.get(user__username=username, id_string=id_string)
    xform.delete()
    return HttpResponseRedirect('/')

def toggle_downloadable(request, username, id_string):
    xform = XForm.objects.get(user__username=username, id_string=id_string)
    xform.downloadable = not xform.downloadable
    xform.save()
    return HttpResponseRedirect("/%s" % username)

