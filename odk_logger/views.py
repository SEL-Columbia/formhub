import json
import os
import tempfile
from xml.parsers.expat import ExpatError
import pytz

from datetime import datetime
from itertools import chain
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseBadRequest, \
    HttpResponseRedirect, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.template import RequestContext, loader
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.contrib import messages
from django.core.files.storage import get_storage_class
from django.core.files import File
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.utils.translation import ugettext as _

from utils.logger_tools import create_instance, OpenRosaResponseBadRequest, \
    OpenRosaResponseNotAllowed, OpenRosaResponse, OpenRosaResponseNotFound,\
    BaseOpenRosaResponse, \
    inject_instanceid, remove_xform, publish_xml_form, publish_form
from models import XForm, Instance
from main.models import UserProfile, MetaData
from utils.logger_tools import response_with_mimetype_and_name
from utils.decorators import is_owner
from utils.user_auth import helper_auth_helper, has_permission,\
    has_edit_permission, HttpResponseNotAuthorized, add_cors_headers
from odk_logger.import_tools import import_instances_from_zip
from odk_logger.xform_instance_parser import InstanceEmptyError,\
    InstanceInvalidUserError, IsNotCrowdformError, DuplicateInstance
from odk_logger.models.instance import FormInactiveError
from odk_logger.models.attachment import Attachment
from utils.log import audit_log, Actions
from django_digest import HttpDigestAuthenticator
from utils.viewer_tools import enketo_url


@require_POST
@csrf_exempt
def bulksubmission(request, username):
    # puts it in a temp directory.
    # runs "import_tools(temp_directory)"
    # deletes
    posting_user = get_object_or_404(User, username=username)

    # request.FILES is a django.utils.datastructures.MultiValueDict
    # for each key we have a list of values
    try:
        temp_postfile = request.FILES.pop("zip_submission_file", [])
    except IOError:
        return HttpResponseBadRequest(_(u"There was a problem receiving your "
                                        u"ODK submission. [Error: IO Error "
                                        u"reading data]"))
    if len(temp_postfile) == 1:
        postfile = temp_postfile[0]
        tempdir = tempfile.gettempdir()
        our_tfpath = os.path.join(tempdir, postfile.name)
        our_tempfile = open(our_tfpath, 'wb')
        our_tempfile.write(postfile.read())
        our_tempfile.close()
        our_tf = open(our_tfpath, 'rb')
        total_count, success_count, errors = \
            import_instances_from_zip(our_tf, user=posting_user)
        # chose the try approach as suggested by the link below
        # http://stackoverflow.com/questions/82831
        try:
            os.remove(our_tfpath)
        except IOError:
            # TODO: log this Exception somewhere
            pass
        json_msg = {
            'message': _(u"Submission complete. Out of %(total)d "
                         u"survey instances, %(success)d were imported, "
                         u"(%(rejected)d were rejected as duplicates, "
                         u"missing forms, etc.)") %
            {'total': total_count, 'success': success_count,
             'rejected': total_count - success_count},
            'errors': u"%d %s" % (len(errors), errors)
        }
        audit = {
            "bulk_submission_log": json_msg
        }
        audit_log(Actions.USER_BULK_SUBMISSION, request.user, posting_user,
                  _("Made bulk submissions."), audit, request)
        response = HttpResponse(json.dumps(json_msg))
        response.status_code = 200
        response['Location'] = request.build_absolute_uri(request.path)
        return response
    else:
        return HttpResponseBadRequest(_(u"There was a problem receiving your"
                                        u" ODK submission. [Error: multiple "
                                        u"submission files (?)]"))


@login_required
def bulksubmission_form(request, username=None):
    if request.user.username == username:
        context = RequestContext(request)
        return render_to_response(
            "bulk_submission_form.html", context_instance=context)
    else:
        return HttpResponseRedirect('/%s' % request.user.username)


@require_GET
def formList(request, username):
    """
    This is where ODK Collect gets its download list.
    """
    if username.lower() == 'crowdforms':
        xforms = XForm.objects.filter(is_crowd_form=True)\
            .exclude(user__username=username)
    else:
        formlist_user = get_object_or_404(User, username=username)
        profile, created = \
            UserProfile.objects.get_or_create(user=formlist_user)

        if profile.require_auth:
            authenticator = HttpDigestAuthenticator()
            if not authenticator.authenticate(request):
                return authenticator.build_challenge_response()

            # unauthorized if user in auth request does not match user in path
            # unauthorized if user not active
            if formlist_user.username != request.user.username or\
                    not request.user.is_active:
                return HttpResponseNotAuthorized()

        xforms = \
            XForm.objects.filter(downloadable=True, user__username=username)
        # retrieve crowd_forms for this user
        crowdforms = XForm.objects.filter(
            metadata__data_type=MetaData.CROWDFORM_USERS,
            metadata__data_value=username
        )
        xforms = chain(xforms, crowdforms)
        audit = {}
        audit_log(Actions.USER_FORMLIST_REQUESTED, request.user, formlist_user,
                  _("Requested forms list."), audit, request)
    response = render_to_response("xformsList.xml", {
        #'urls': urls,
        'host': request.build_absolute_uri().replace(
            request.get_full_path(), ''),
        'xforms': xforms
    }, mimetype="text/xml; charset=utf-8")
    response['X-OpenRosa-Version'] = '1.0'
    tz = pytz.timezone(settings.TIME_ZONE)
    dt = datetime.now(tz).strftime('%a, %d %b %Y %H:%M:%S %Z')
    response['Date'] = dt
    return response


@require_GET
def xformsManifest(request, username, id_string):
    xform = get_object_or_404(
        XForm, id_string=id_string, user__username=username)
    formlist_user = xform.user
    profile, created = \
        UserProfile.objects.get_or_create(user=formlist_user)

    if profile.require_auth:
        authenticator = HttpDigestAuthenticator()
        if not authenticator.authenticate(request):
            return authenticator.build_challenge_response()
    response = render_to_response("xformsManifest.xml", {
        #'urls': urls,
        'host': request.build_absolute_uri().replace(
            request.get_full_path(), ''),
        'media_files': MetaData.media_upload(xform)
    }, mimetype="text/xml; charset=utf-8")
    response['X-OpenRosa-Version'] = '1.0'
    tz = pytz.timezone(settings.TIME_ZONE)
    dt = datetime.now(tz).strftime('%a, %d %b %Y %H:%M:%S %Z')
    response['Date'] = dt
    return response


@require_http_methods(["HEAD", "POST"])
@csrf_exempt
def submission(request, username=None):
    if username and username.lower() != 'crowdforms':
        formlist_user = get_object_or_404(User, username=username.lower())
        profile, created = \
            UserProfile.objects.get_or_create(user=formlist_user)

        if profile.require_auth:
            authenticator = HttpDigestAuthenticator()
            if not authenticator.authenticate(request):
                return authenticator.build_challenge_response()
    if request.method == 'HEAD':
        response = OpenRosaResponse(status=204)
        if username:
            response['Location'] = request.build_absolute_uri().replace(
                request.get_full_path(), '/%s/submission' % username)
        else:
            response['Location'] = request.build_absolute_uri().replace(
                request.get_full_path(), '/submission')
        return response
    context = RequestContext(request)
    xml_file_list = []
    media_files = []
    html_response = False
    # request.FILES is a django.utils.datastructures.MultiValueDict
    # for each key we have a list of values
    try:
        xml_file_list = request.FILES.pop("xml_submission_file", [])
        if len(xml_file_list) != 1:
            return OpenRosaResponseBadRequest(
                _(u"There should be a single XML submission file.")
            )
        # save this XML file and media files as attachments
        media_files = request.FILES.values()

        # get uuid from post request
        uuid = request.POST.get('uuid')
        # response as html if posting with a UUID
        if not username and uuid:
            html_response = True
        try:
            instance = create_instance(
                username, xml_file_list[0], media_files,
                uuid=uuid, request=request
            )
        except InstanceInvalidUserError:
            return OpenRosaResponseBadRequest(_(u"Username or ID required."))
        except IsNotCrowdformError:
            return OpenRosaResponseNotAllowed(
                _(u"Sorry but the crowd form you submitted to is closed.")
            )
        except InstanceEmptyError:
            return OpenRosaResponseBadRequest(
                _(u"Received empty submission. No instance was created")
            )
        except FormInactiveError:
            return OpenRosaResponseNotAllowed(_(u"Form is not active"))
        except XForm.DoesNotExist:
            return OpenRosaResponseNotFound(
                _(u"Form does not exist on this account")
            )
        except ExpatError:
            return OpenRosaResponseBadRequest(_(u"Improperly formatted XML."))
        except DuplicateInstance:
            response = OpenRosaResponse(_(u"Duplicate submission"))
            response.status_code = 202
            response['Location'] = request.build_absolute_uri(request.path)
            return response
        except PermissionDenied, e:
            return OpenRosaResponseNotAllowed(e.message)
        except Exception, e:
            raise

        if instance is None:
            return OpenRosaResponseBadRequest(
                _(u"Unable to create submission."))

        audit = {
            "xform": instance.xform.id_string
        }
        audit_log(
            Actions.SUBMISSION_CREATED, request.user, instance.xform.user,
            _("Created submission on form %(id_string)s.") %
            {
                "id_string": instance.xform.id_string
            }, audit, request)
        # ODK needs two things for a form to be considered successful
        # 1) the status code needs to be 201 (created)
        # 2) The location header needs to be set to the host it posted to
        if html_response:
            context.username = instance.user.username
            context.id_string = instance.xform.id_string
            context.domain = Site.objects.get(id=settings.SITE_ID).domain
            response = render_to_response("submission.html",
                                          context_instance=context)
        else:
            context.message = _("Successful submission.")
            context.formid = instance.xform.id_string
            context.encrypted = instance.xform.encrypted
            context.instanceID = u'uuid:%s' % instance.uuid
            context.submissionDate = instance.date_created.isoformat()
            context.markedAsCompleteDate = instance.date_modified.isoformat()
            t = loader.get_template('submission.xml')
            response = BaseOpenRosaResponse(t.render(context))
        response.status_code = 201
        response['Location'] = request.build_absolute_uri(request.path)
        return response
    except IOError as e:
        if 'request data read error' in unicode(e):
            return OpenRosaResponseBadRequest(
                _(u"File transfer interruption."))
        else:
            raise
    finally:
        if len(xml_file_list):
            [_file.close() for _file in xml_file_list]
        if len(media_files):
            [_file.close() for _file in media_files]


def download_xform(request, username, id_string):
    user = get_object_or_404(User, username=username)
    xform = get_object_or_404(XForm,
                              user=user, id_string=id_string)
    profile, created =\
        UserProfile.objects.get_or_create(user=user)

    if profile.require_auth:
        authenticator = HttpDigestAuthenticator()
        if not authenticator.authenticate(request):
            return authenticator.build_challenge_response()
    audit = {
        "xform": xform.id_string
    }
    audit_log(
        Actions.FORM_XML_DOWNLOADED, request.user, xform.user,
        _("Downloaded XML for form '%(id_string)s'.") %
        {
            "id_string": xform.id_string
        }, audit, request)
    response = response_with_mimetype_and_name('xml', id_string,
                                               show_date=False)
    response.content = xform.xml
    return response


def download_xlsform(request, username, id_string):
    xform = get_object_or_404(XForm,
                              user__username=username, id_string=id_string)
    owner = User.objects.get(username=username)
    helper_auth_helper(request)
    if not has_permission(xform, owner, request, xform.shared):
        return HttpResponseForbidden('Not shared.')
    file_path = xform.xls.name
    default_storage = get_storage_class()()
    if default_storage.exists(file_path):
        audit = {
            "xform": xform.id_string
        }
        audit_log(
            Actions.FORM_XLS_DOWNLOADED, request.user, xform.user,
            _("Downloaded XLS file for form '%(id_string)s'.") %
            {
                "id_string": xform.id_string
            }, audit, request)
        split_path = file_path.split(os.extsep)
        extension = 'xls'
        if len(split_path) > 1:
            extension = split_path[len(split_path) - 1]
        response = response_with_mimetype_and_name(
            'vnd.ms-excel', id_string, show_date=False, extension=extension,
            file_path=file_path)
        return response
    else:
        messages.add_message(request, messages.WARNING,
                             _(u'No XLS file for your form '
                               u'<strong>%(id)s</strong>')
                             % {'id': id_string})
        return HttpResponseRedirect("/%s" % username)


def download_jsonform(request, username, id_string):
    owner = get_object_or_404(User, username=username)
    xform = get_object_or_404(XForm, user__username=username,
                              id_string=id_string)
    if request.method == "OPTIONS":
        response = HttpResponse()
        add_cors_headers(response)
        return response
    helper_auth_helper(request)
    if not has_permission(xform, owner, request, xform.shared):
        response = HttpResponseForbidden(_(u'Not shared.'))
        add_cors_headers(response)
        return response
    response = response_with_mimetype_and_name('json', id_string,
                                               show_date=False)
    if 'callback' in request.GET and request.GET.get('callback') != '':
        callback = request.GET.get('callback')
        response.content = "%s(%s)" % (callback, xform.json)
    else:
        add_cors_headers(response)
        response.content = xform.json
    return response


@is_owner
@require_POST
def delete_xform(request, username, id_string):
    xform = get_object_or_404(XForm, user__username=username,
                              id_string=id_string)

    # delete xform and submissions
    remove_xform(xform)

    audit = {}
    audit_log(
        Actions.FORM_DELETED, request.user, xform.user,
        _("Deleted form '%(id_string)s'.") %
        {
            'id_string': xform.id_string,
        }, audit, request)
    return HttpResponseRedirect('/')


@is_owner
def toggle_downloadable(request, username, id_string):
    xform = XForm.objects.get(user__username=username, id_string=id_string)
    xform.downloadable = not xform.downloadable
    xform.save()
    audit = {}
    audit_log(
        Actions.FORM_UPDATED, request.user, xform.user,
        _("Made form '%(id_string)s' %(downloadable)s.") %
        {
            'id_string': xform.id_string,
            'downloadable':
            _("downloadable") if xform.downloadable else _("un-downloadable")
        }, audit, request)
    return HttpResponseRedirect("/%s" % username)


def enter_data(request, username, id_string):
    owner = get_object_or_404(User, username=username)
    xform = get_object_or_404(XForm, user__username=username,
                              id_string=id_string)
    if not has_edit_permission(xform, owner, request, xform.shared):
        return HttpResponseForbidden(_(u'Not shared.'))
    try:
        formhub_url = "http://%s/" % request.META['HTTP_HOST']
    except:
        formhub_url = "http://formhub.org/"
    form_url = formhub_url + username
    if settings.TESTING_MODE:
        form_url = "https://testserver.com/bob"
    try:
        url = enketo_url(form_url, xform.id_string)
        if not url:
            return HttpResponseRedirect(reverse('main.views.show',
                                        kwargs={'username': username,
                                                'id_string': id_string}))
        return HttpResponseRedirect(url)
    except Exception, e:
        context = RequestContext(request)
        owner = User.objects.get(username=username)
        context.profile, created = \
            UserProfile.objects.get_or_create(user=owner)
        context.xform = xform
        context.content_user = owner
        context.form_view = True
        context.message = {
            'type': 'alert-error',
            'text': u"Enketo error, reason: %s" % e}
        messages.add_message(
            request, messages.WARNING,
            _("Enketo error: enketo replied %s") % e, fail_silently=True)
        return render_to_response("profile.html", context_instance=context)
    return HttpResponseRedirect(reverse('main.views.show',
                                kwargs={'username': username,
                                        'id_string': id_string}))


def edit_data(request, username, id_string, data_id):
    context = RequestContext(request)
    owner = User.objects.get(username=username)
    xform = get_object_or_404(
        XForm, user__username=username, id_string=id_string)
    instance = get_object_or_404(
        Instance, pk=data_id, xform=xform)
    if not has_edit_permission(xform, owner, request, xform.shared):
        return HttpResponseForbidden(_(u'Not shared.'))
    if not hasattr(settings, 'ENKETO_URL'):
        return HttpResponseRedirect(
            reverse(
                'main.views.show', kwargs={'username': username,
                                           'id_string': id_string}
            )
        )

    url = '%sdata/edit_url' % settings.ENKETO_URL
    # see commit 220f2dad0e for tmp file creation
    try:
        formhub_url = "http://%s/" % request.META['HTTP_HOST']
    except:
        formhub_url = "http://formhub.org/"
    injected_xml = inject_instanceid(instance.xml, instance.uuid)
    return_url = request.build_absolute_uri(
        reverse(
            'odk_viewer.views.instance',
            kwargs={
                'username': username,
                'id_string': id_string}
        ) + "#/" + str(instance.id))
    form_url = formhub_url + username
    if settings.TESTING_MODE:
        form_url = "https://testserver.com/bob"
    try:
        url = enketo_url(
            form_url, xform.id_string, instance_xml=injected_xml,
            instance_id=instance.uuid, return_url=return_url
        )
    except Exception, e:
        context.message = {
            'type': 'alert-error',
            'text': u"Enketo error, reason: %s" % e}
        messages.add_message(
            request, messages.WARNING,
            _("Enketo error: enketo replied %s") % e, fail_silently=True)
    else:
        if url:
            context.enketo = url
            return HttpResponseRedirect(url)
    return HttpResponseRedirect(
        reverse('main.views.show',
                kwargs={'username': username,
                        'id_string': id_string}))


def view_submission_list(request, username):
    form_user = get_object_or_404(User, username=username)
    profile, created = \
        UserProfile.objects.get_or_create(user=form_user)
    authenticator = HttpDigestAuthenticator()
    if not authenticator.authenticate(request):
        return authenticator.build_challenge_response()
    context = RequestContext(request)
    id_string = request.GET.get('formId', None)
    xform = get_object_or_404(
        XForm, id_string=id_string, user__username=username)
    if not has_permission(xform, form_user, request, xform.shared_data):
        return HttpResponseForbidden('Not shared.')
    num_entries = request.GET.get('numEntries', None)
    cursor = request.GET.get('cursor', None)
    instances = xform.surveys.all().order_by('pk')

    if cursor:
        try:
            cursor = int(cursor)
        except ValueError:
            pass
        else:
            instances = instances.filter(pk__gt=cursor)

    if num_entries:
        try:
            num_entries = int(num_entries)
        except ValueError:
            pass
        else:
            instances = instances[:num_entries]
    context.instances = instances

    if instances.count():
        last_instance = instances[instances.count() - 1]
        context.resumptionCursor = last_instance.pk
    elif instances.count() == 0 and cursor:
        context.resumptionCursor = cursor
    else:
        context.resumptionCursor = 0

    return render_to_response(
        'submissionList.xml', context_instance=context,
        mimetype="text/xml; charset=utf-8")


def view_download_submission(request, username):

    def extract_uuid(text):
        text = text[text.find("@key="):-1].replace("@key=", "")
        if text.startswith("uuid:"):
            text = text.replace("uuid:", "")
        return text

    form_user = get_object_or_404(User, username=username)
    profile, created = \
        UserProfile.objects.get_or_create(user=form_user)
    authenticator = HttpDigestAuthenticator()
    if not authenticator.authenticate(request):
        return authenticator.build_challenge_response()
    context = RequestContext(request)
    formId = request.GET.get('formId', None)
    if not isinstance(formId, basestring):
        return HttpResponseBadRequest()

    id_string = formId[0:formId.find('[')]
    form_id_parts = formId.split('/')
    if form_id_parts.__len__() < 2:
        return HttpResponseBadRequest()

    uuid = extract_uuid(form_id_parts[1])
    instance = get_object_or_404(
        Instance, xform__id_string=id_string, uuid=uuid,
        user__username=username)
    xform = instance.xform
    if not has_permission(xform, form_user, request, xform.shared_data):
        return HttpResponseForbidden('Not shared.')
    submission_xml_root_node = instance.get_root_node()
    submission_xml_root_node.setAttribute(
        'instanceID', u'uuid:%s' % instance.uuid)
    submission_xml_root_node.setAttribute(
        'submissionDate', instance.date_created.isoformat()
    )
    context.submission_data = submission_xml_root_node.toxml()
    context.media_files = Attachment.objects.filter(instance=instance)
    context.host = request.build_absolute_uri().replace(
        request.get_full_path(), '')
    return render_to_response(
        'downloadSubmission.xml', context_instance=context,
        mimetype="text/xml; charset=utf-8")


@require_http_methods(["HEAD", "POST"])
@csrf_exempt
def form_upload(request, username):
    class DoXmlFormUpload():
        def __init__(self, xml_file, user):
            self.xml_file = xml_file
            self.user = user

        def publish(self):
            return publish_xml_form(self.xml_file, self.user)

    form_user = get_object_or_404(User, username=username)
    profile, created = \
        UserProfile.objects.get_or_create(user=form_user)
    authenticator = HttpDigestAuthenticator()
    if not authenticator.authenticate(request):
        return authenticator.build_challenge_response()
    if form_user != request.user:
        return HttpResponseForbidden(
            _(u"Not allowed to upload form[s] to %(user)s account." %
              {'user': form_user}))
    if request.method == 'HEAD':
        response = OpenRosaResponse(status=204)
        response['Location'] = request.build_absolute_uri().replace(
            request.get_full_path(), '/%s/formUpload' % form_user.username)
        return response
    xform_def = request.FILES.get('form_def_file', None)
    content = u""
    if isinstance(xform_def, File):
        do_form_upload = DoXmlFormUpload(xform_def, form_user)
        dd = publish_form(do_form_upload.publish)
        status = 201
        if isinstance(dd, XForm):
            content = _(u"%s successfully published." % dd.id_string)
        else:
            content = dd['text']
            if isinstance(content, Exception):
                content = content.message
                status = 500
            else:
                status = 400
    return OpenRosaResponse(content, status=status)
