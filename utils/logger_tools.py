from datetime import date, datetime
import decimal
import os
import pytz
import re
import tempfile
import traceback

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.storage import get_storage_class
from django.core.mail import mail_admins
from django.core.servers.basehttp import FileWrapper
from django.db import IntegrityError
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from modilabs.utils.subprocess_timeout import ProcessTimedOut
from pyxform.errors import PyXFormError

from odk_logger.models import Attachment
from odk_logger.models import Instance
from odk_logger.models.instance import InstanceHistory
from odk_logger.models import XForm
from odk_logger.models.xform import XLSFormError
from odk_logger.xform_instance_parser import InstanceInvalidUserError, \
    IsNotCrowdformError, DuplicateInstance, clean_and_parse_xml, \
    get_uuid_from_xml, get_deprecated_uuid_from_xml

from odk_viewer.models import ParsedInstance, DataDictionary


OPEN_ROSA_VERSION_HEADER = 'X-OpenRosa-Version'
HTTP_OPEN_ROSA_VERSION_HEADER = 'HTTP_X_OPENROSA_VERSION'
OPEN_ROSA_VERSION = '1.0'
DEFAULT_CONTENT_TYPE = 'text/xml; charset=utf-8'
DEFAULT_CONTENT_LENGTH = 5000000

uuid_regex = re.compile(r'<formhub><uuid>([^<]+)</uuid></formhub>',
                        re.DOTALL)


@transaction.commit_on_success
def create_instance(username, xml_file, media_files,
                    status=u'submitted_via_web', uuid=None):
    """
    I used to check if this file had been submitted already, I've
    taken this out because it was too slow. Now we're going to create
    a way for an admin to mark duplicate instances. This should
    simplify things a bit.
    Submission cases:
        If there is a username and no uuid, submitting an old ODK form.
        If there is no username and a uuid, submitting a touchform.
        If there is a username and a uuid, submitting a new ODK form.
    """
    xml = xml_file.read()
    is_touchform = False
    # check alternative form submission ids
    if not uuid:
        # parse UUID from uploaded XML
        split_xml = uuid_regex.split(xml)

        # check that xml has UUID, then it is a crowdform
        if len(split_xml) > 1:
            uuid = split_xml[1]
    else:
        # is a touchform
        is_touchform = True

    if not username and not uuid:
        raise InstanceInvalidUserError()

    if uuid:
        # try find the fomr by its uuid which is the ideal condition
        if XForm.objects.filter(uuid=uuid).count() > 0:
            xform = XForm.objects.get(uuid=uuid)
            xform_username = xform.user.username

            if xform_username != username and not xform.is_crowd_form \
                    and not is_touchform:
                raise IsNotCrowdformError()

            username = xform_username
    # else, since we have a username, the Instance creation logic will handle checking for the forms existence by its id_string

    user = get_object_or_404(User, username=username)
    existing_instance_count = Instance.objects.filter(
        xml=xml, user=user).count()

    if existing_instance_count == 0:
        proceed_to_create_instance = True
    else:
        existing_instance = Instance.objects.filter(xml=xml, user=user)[0]
        if existing_instance.xform and\
                not existing_instance.xform.has_start_time:
            proceed_to_create_instance = True
        else:
            # Ignore submission as a duplicate IFF
            #  * a submission's XForm collects start time
            #  * the submitted XML is an exact match with one that
            #    has already been submitted for that user.
            proceed_to_create_instance = False
            raise DuplicateInstance()

    # get new and depracated uuid's
    new_uuid = get_uuid_from_xml(xml)
    duplicate_instances = Instance.objects.filter(uuid=new_uuid)
    if duplicate_instances:
        raise DuplicateInstance()

    if proceed_to_create_instance:
        # check if its an edit submission
        old_uuid = get_deprecated_uuid_from_xml(xml)
        instances = Instance.objects.filter(uuid=old_uuid)
        if instances:
            instance = instances[0]
            InstanceHistory.objects.create(
                xml=instance.xml, xform_instance=instance, uuid=old_uuid)
            instance.xml = xml
            instance.uuid = new_uuid
            instance.save()
        else:
            # new submission
            instance = Instance.objects.create(
                xml=xml, user=user, status=status)
        for f in media_files:
            Attachment.objects.get_or_create(instance=instance, media_file=f)
        if instance.xform is not None:
            pi, created = ParsedInstance.objects.get_or_create(
                instance=instance)
            if not created:
                pi.update_mongo(edit=True)
        return instance
    return None


def report_exception(subject, info, exc_info=None):
    if exc_info:
        cls, err = exc_info[:2]
        info += _(u"Exception in request: %(class)s: %(error)s")\
            % {'class': cls.__name__, 'error': err}
        info += u"".join(traceback.format_exception(*exc_info))

    if settings.DEBUG or settings.TESTING_MODE:
        print subject
        print info
    else:
        mail_admins(subject=subject, message=info)


def round_down_geopoint(num):
    if num:
        decimal_mult = 1000000
        return str(decimal.Decimal(int(num * decimal_mult)) / decimal_mult)
    return None


def response_with_mimetype_and_name(
        mimetype, name, extension=None, show_date=True, file_path=None,
        use_local_filesystem=False, full_mime=False):
    if extension is None:
        extension = mimetype
    if not full_mime:
        mimetype = "application/%s" % mimetype
    if file_path:
        if not use_local_filesystem:
            default_storage = get_storage_class()()
            wrapper = FileWrapper(default_storage.open(file_path))
            response = HttpResponse(wrapper, mimetype=mimetype)
            response['Content-Length'] = default_storage.size(file_path)
        else:
            wrapper = FileWrapper(file(file_path))
            response = HttpResponse(wrapper, mimetype=mimetype)
            response['Content-Length'] = os.path.getsize(file_path)
    else:
        response = HttpResponse(mimetype=mimetype)
    response['Content-Disposition'] = disposition_ext_and_date(
        name, extension, show_date)
    return response


def disposition_ext_and_date(name, extension, show_date=True):
    if name is None:
        return 'attachment;'
    if show_date:
        name = "%s_%s" % (name, date.today().strftime("%Y_%m_%d"))
    return 'attachment; filename=%s.%s' % (name, extension)


def store_temp_file(data):
    tmp = tempfile.TemporaryFile()
    ret = None
    try:
        tmp.write(data)
        tmp.seek(0)
        ret = tmp
    finally:
        tmp.close()
    return ret


def publish_form(callback):
    try:
        return callback()
    except (PyXFormError, XLSFormError) as e:
        return {
            'type': 'alert-error',
            'text': unicode(e),
        }
    except IntegrityError as e:
        return {
            'type': 'alert-error',
            'text': _(u'Form with this id already exists.'),
        }
    except ValidationError as e:
        # on clone invalid URL
        return {
            'type': 'alert-error',
            'text': _(u'Invalid URL format.'),
        }
    except AttributeError as e:
        # form.publish returned None, not sure why...
        return {
            'type': 'alert-error',
            'text': unicode(e),
        }
    except ProcessTimedOut as e:
        # catch timeout errors
        return {
            'type': 'alert-error',
            'text': _('Form validation timeout, please try again.'),
        }

def publish_xls_form(xls_file, user, id_string=None):
    """
    Creates or updates a DataDictionary with supplied xls_file, user and optional id_string - if updating
    """
    # get or create DataDictionary based on user and id string
    if id_string:
        dd = DataDictionary.objects.get(user=user,
            id_string=id_string)
        dd.xls = xls_file
        dd.save()
        return dd
    else:
        return DataDictionary.objects.create(
            user=user,
            xls=xls_file
        )



class OpenRosaResponse(HttpResponse):
    status_code = 201

    def __init__(self, *args, **kwargs):
        super(OpenRosaResponse, self).__init__(*args, **kwargs)

        self[OPEN_ROSA_VERSION_HEADER] = OPEN_ROSA_VERSION
        tz = pytz.timezone(settings.TIME_ZONE)
        dt = datetime.now(tz).strftime('%a, %d %b %Y %H:%M:%S %Z')
        self['Date'] = dt
        self['X-OpenRosa-Accept-Content-Length'] = DEFAULT_CONTENT_LENGTH
        self['Content-Type'] = DEFAULT_CONTENT_TYPE
        # wrap content around xml
        self.content = '''<?xml version='1.0' encoding='UTF-8' ?>
<OpenRosaResponse xmlns="http://openrosa.org/http/response">
        <message nature="">%s</message>
</OpenRosaResponse>''' % self.content


class OpenRosaResponseNotFound(OpenRosaResponse):
    status_code = 404


class OpenRosaResponseBadRequest(OpenRosaResponse):
    status_code = 400


class OpenRosaResponseNotAllowed(OpenRosaResponse):
    status_code = 405


def inject_instanceid(instance):
    if get_uuid_from_xml(instance.xml) is None:
        xml = clean_and_parse_xml(instance.xml)
        children = xml.childNodes
        # insert meta and instanceID
        text_node = xml.createTextNode(u"uuid:%s" % instance.uuid)
        instanceid_tag = xml.createElement("instanceID")
        instanceid_tag.appendChild(text_node)
        meta_tag = xml.createElement("meta")
        meta_tag.appendChild(instanceid_tag)
        xml.documentElement.appendChild(meta_tag)
        return xml.toxml()
    return instance.xml
