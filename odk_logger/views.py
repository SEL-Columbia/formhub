import base64
import json
import os
import tempfile
import urllib, urllib2
import zipfile

from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseBadRequest, \
    HttpResponseRedirect, HttpResponseForbidden, HttpResponseNotAllowed
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib.sites.models import Site
from django.contrib import messages
from django.core.files.storage import get_storage_class
from django.core.files.base import ContentFile
from django.core.urlresolvers import reverse
from django.conf import settings
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers

from utils.logger_tools import create_instance
from models import XForm
from main.models import UserProfile, MetaData
from utils.logger_tools import response_with_mimetype_and_name, store_temp_file
from utils.decorators import is_owner
from utils.user_auth import has_permission, has_edit_permission
from odk_logger.import_tools import import_instances_from_zip
from odk_logger.xform_instance_parser import InstanceEmptyError
from odk_logger.models.instance import FormInactiveError

class HttpResponseNotAuthorized(HttpResponse):
    status_code = 401

    def __init__(self, redirect_to):
        HttpResponse.__init__(self)
        self['WWW-Authenticate'] =\
                'Basic realm="%s"' % Site.objects.get_current().name

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
    try:
        temp_postfile = request.FILES.pop("zip_submission_file", [])
    except IOError:
        return HttpResponseBadRequest("There was a problem receiving your ODK submission. [Error: IO Error reading data]")
    if len(temp_postfile) == 1:
        postfile = temp_postfile[0]
        tempdir = tempfile.gettempdir()
        our_tfpath = os.path.join(tempdir, postfile.name)
        our_tempfile = open(our_tfpath, 'wb')
        our_tempfile.write(postfile.read())
        our_tempfile.close()
        our_tf = open(our_tfpath, 'rb')
        total_count, success_count, errors = import_instances_from_zip(our_tf, user=posting_user)
        os.remove(our_tfpath)
        json_msg = {
            'message': "Submission successful. Out of %d survey instances, %d were imported (%d were rejected--duplicates, missing forms, etc.)" % \
                    (total_count, success_count, total_count - success_count),
            'errors': "%d %s" % (len(errors), errors)
        }
        response = HttpResponse(json.dumps(json_msg))
        response.status_code = 200
        response['Location'] = request.build_absolute_uri(request.path)
        return response
    else:
        return HttpResponseBadRequest("There was a problem receiving your ODK submission. [Error: multiple submission files (?)]")

@login_required
def bulksubmission_form(request, username=None):
    if request.user.username == username:
        return render_to_response("bulk_submission_form.html")
    else:
        return HttpResponseRedirect('/%s' % request.user.username)


@require_GET
def formList(request, username):
    render_formlist = False
    formlist_user = get_object_or_404(User, username=username)
    profile, created = UserProfile.objects.get_or_create(user=formlist_user)
    if profile.require_auth:
        # source, http://djangosnippets.org/snippets/243/
        if 'HTTP_AUTHORIZATION' in request.META:
            auth = request.META['HTTP_AUTHORIZATION'].split()
            # NOTE: We are only support BASIC authentication for now.
            if len(auth) == 2 and auth[0].lower() == "basic":
                uname, passwd = base64.b64decode(auth[1]).split(':')
                # ensure listing this user's forms
                if formlist_user.username == uname:
                    user = authenticate(username=uname, password=passwd)
                    if user is not None and user.is_active:
                        render_formlist = True
    else:
        render_formlist = True
    if render_formlist:
        """This is where ODK Collect gets its download list."""
        xforms = XForm.objects.filter(downloadable=True, user__username=username)
        urls = [
            {'url': request.build_absolute_uri(xform.url()), 'text': xform.title
            , 'media': {'m': MetaData.media_upload(xform), 'user': xform.user, 
            'id': xform.id_string}}
            for xform in xforms
        ]
        return render_to_response("formList.xml", {'urls': urls, 'host': 
                        'http://%s' % request.get_host()}, mimetype="text/xml")
    return HttpResponseNotAuthorized('Must be logged in')


@require_POST
@csrf_exempt
def submission(request, username=None):
    context = RequestContext(request)
    show_options = False
    # request.FILES is a django.utils.datastructures.MultiValueDict
    # for each key we have a list of values
    try:
        xml_file_list = request.FILES.pop("xml_submission_file", [])
    except IOError, e:
        if type(e) == tuple:
            e = e[1]
        if str(e) == 'request data read error':
            return HttpResponseBadRequest("File transfer interruption.")
        else:
            raise
    if len(xml_file_list) != 1:
        return HttpResponseBadRequest(
            "There should be a single XML submission file."
            )
    # save this XML file and media files as attachments
    media_files = request.FILES.values()
    if not username:
        uuid = request.POST.get('uuid')
        if not uuid:
            return HttpResponseBadRequest("Username or ID required.")
        show_options = True
        xform = XForm.objects.get(uuid=uuid)
        username = xform.user.username
    try:
        instance = create_instance(
                username,
                xml_file_list[0],
                media_files
                )
    except InstanceEmptyError:
        return HttpResponseBadRequest('Received empty submission. No instance was created')
    except FormInactiveError:
        return HttpResponseNotAllowed('Form is not active')
    if instance == None:
        return HttpResponseBadRequest("Unable to create submission.")
    # ODK needs two things for a form to be considered successful
    # 1) the status code needs to be 201 (created)
    # 2) The location header needs to be set to the host it posted to
    if show_options:
        context.username = instance.user.username
        context.id_string = instance.xform.id_string
        context.domain = Site.objects.get(id=settings.SITE_ID).domain
        response = render_to_response("submission.html",
            context_instance=context)
    else:
        response = HttpResponse()
    response.status_code = 201
    response['Location'] = request.build_absolute_uri(request.path)
    return response

def download_xform(request, username, id_string):
    xform = get_object_or_404(XForm,
            user__username=username, id_string=id_string)
    # TODO: protect for users who have settings to use auth
    response = response_with_mimetype_and_name('xml', id_string,
        show_date=False)
    response.content = xform.xml
    return response

def download_xlsform(request, username, id_string):
    xform = get_object_or_404(XForm,
            user__username=username, id_string=id_string)
    owner = User.objects.get(username=username)
    if not has_permission(xform, owner, request, xform.shared):
        return HttpResponseForbidden('Not shared.')
    file_path = xform.xls.name
    default_storage = get_storage_class()()
    if default_storage.exists(file_path):
        response = response_with_mimetype_and_name('vnd.ms-excel', id_string,
                show_date=False, extension='xls', file_path=file_path)
        return response
    else:
        messages.add_message(request, messages.WARNING,
                'No XLS file for your form <strong>%s</strong>' % id_string)
        return HttpResponseRedirect("/%s" % username)

def download_jsonform(request, username, id_string):
    owner = get_object_or_404(User, username=username)
    xform = get_object_or_404(XForm, user__username=username,
            id_string=id_string)
    if not has_permission(xform, owner, request, xform.shared):
        return HttpResponseForbidden('Not shared.')
    response = response_with_mimetype_and_name('json', id_string,
            show_date=False)
    if 'callback' in request.GET and request.GET.get('callback') != '':
        callback = request.GET.get('callback')
        response.content = "%s(%s)" % (callback, xform.json)
    else:
        response.content = xform.json
    return response

@is_owner
def delete_xform(request, username, id_string):
    xform = get_object_or_404(XForm, user__username=username,
        id_string=id_string)
    xform.delete()
    return HttpResponseRedirect('/')

@is_owner
def toggle_downloadable(request, username, id_string):
    xform = XForm.objects.get(user__username=username, id_string=id_string)
    xform.downloadable = not xform.downloadable
    xform.save()
    return HttpResponseRedirect("/%s" % username)

def enter_data(request, username, id_string):
    owner = User.objects.get(username=username)
    xform = get_object_or_404(XForm, user__username=username,
                id_string=id_string)
    if not has_edit_permission(xform, owner, request, xform.shared):
        return HttpResponseForbidden('Not shared.')
    if not hasattr(settings, 'TOUCHFORMS_URL'):
        return HttpResponseRedirect(reverse('main.views.show',
            kwargs={'username': username, 'id_string': id_string}))
    url = settings.TOUCHFORMS_URL
    register_openers()
    response = None
    with tempfile.TemporaryFile() as tmp:
        tmp.write(xform.xml.encode('utf-8'))
        tmp.seek(0)
        values = {
            'file': tmp,
            'format': 'json',
            'uuid': xform.uuid
        }
        data, headers = multipart_encode(values)
        headers['User-Agent'] = 'formhub'
        req = urllib2.Request(url, data, headers)
        try:
            response = urllib2.urlopen(req)
            response = json.loads(response.read())
            context = RequestContext(request)
            owner = User.objects.get(username=username)
            context.profile, created = UserProfile.objects.get_or_create(
                    user=owner)
            context.xform = xform
            context.content_user = owner
            context.form_view = True
            context.touchforms = response['url']
            return render_to_response("form_entry.html",
context_instance=context)
            #return HttpResponseRedirect(response['url'])
        except urllib2.URLError:
            pass # this will happen if we could not connect to touchforms
    return HttpResponseRedirect(reverse('main.views.show',
                kwargs={'username': username, 'id_string': id_string}))
