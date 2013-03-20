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
from django.db.models.signals import pre_delete
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from modilabs.utils.subprocess_timeout import ProcessTimedOut
from pyxform.errors import PyXFormError
import sys
import common_tags

from odk_logger.models import Attachment
from odk_logger.models import Instance
from odk_logger.models.instance import InstanceHistory
from odk_logger.models import XForm
from odk_logger.models.xform import XLSFormError
from odk_logger.xform_instance_parser import InstanceInvalidUserError, \
    IsNotCrowdformError, DuplicateInstance, clean_and_parse_xml, \
    get_uuid_from_xml, get_deprecated_uuid_from_xml
from odk_viewer.models.parsed_instance import _remove_from_mongo
from odk_viewer.models.parsed_instance import xform_instances

from odk_viewer.models import ParsedInstance, DataDictionary
from utils.model_tools import queryset_iterator
from xml.dom import Node


OPEN_ROSA_VERSION_HEADER = 'X-OpenRosa-Version'
HTTP_OPEN_ROSA_VERSION_HEADER = 'HTTP_X_OPENROSA_VERSION'
OPEN_ROSA_VERSION = '1.0'
DEFAULT_CONTENT_TYPE = 'text/xml; charset=utf-8'
DEFAULT_CONTENT_LENGTH = 5000000

uuid_regex = re.compile(r'<formhub><uuid>([^<]+)</uuid></formhub>',
                        re.DOTALL)

mongo_instances = settings.MONGO_DB.instances


@transaction.commit_manually
def create_instance(username, xml_file, media_files,
                    status=u'submitted_via_web', uuid=None,
                    date_created_override=None):
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
    try:
        if username:
            username = username.lower()
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
        # else, since we have a username, the Instance creation logic will
        # handle checking for the forms existence by its id_string

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
            for f in media_files:
                Attachment.objects.get_or_create(
                    instance=duplicate_instances[0],
                    media_file=f, mimetype=f.content_type)
            # ensure we have saved the extra attachments
            transaction.commit()
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
                Attachment.objects.get_or_create(
                    instance=instance, media_file=f, mimetype=f.content_type)

            # override date created if required
            if date_created_override:
                instance.date_created = date_created_override
                instance.save()

            if instance.xform is not None:
                pi, created = ParsedInstance.objects.get_or_create(
                    instance=instance)
            if not created:
                pi.save(async=False)
        # commit all changes
        transaction.commit()
        return instance
    except Exception:
        transaction.rollback()
        raise
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
        try:
            if not use_local_filesystem:
                default_storage = get_storage_class()()
                wrapper = FileWrapper(default_storage.open(file_path))
                response = HttpResponse(wrapper, mimetype=mimetype)
                response['Content-Length'] = default_storage.size(file_path)
            else:
                wrapper = FileWrapper(file(file_path))
                response = HttpResponse(wrapper, mimetype=mimetype)
                response['Content-Length'] = os.path.getsize(file_path)
        except IOError:
            response = HttpResponseNotFound(
                _(u"The requested file could not be found."))
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
            'text': e
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
            'text': e
        }
    except ProcessTimedOut as e:
        # catch timeout errors
        return {
            'type': 'alert-error',
            'text': _(u'Form validation timeout, please try again.'),
        }
    except Exception, e:
        report_exception("ERROR: XLSForm publishing Exception", e)
        return {
            'type': 'alert-error',
            'text': e
        }


def publish_xls_form(xls_file, user, id_string=None):
    """ Creates or updates a DataDictionary with supplied xls_file,
        user and optional id_string - if updating
    """
    # get or create DataDictionary based on user and id string
    if id_string:
        dd = DataDictionary.objects.get(
            user=user, id_string=id_string)
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


def inject_instanceid(xml_str, uuid):
    if get_uuid_from_xml(xml_str) is None:
        xml = clean_and_parse_xml(xml_str)
        children = xml.childNodes
        if children.length == 0:
            raise ValueError(_("XML string must have a survey element."))

        # check if we have a meta tag
        survey_node = children.item(0)
        meta_tags = [
            n for n in survey_node.childNodes
            if n.nodeType == Node.ELEMENT_NODE
            and n.tagName.lower() == "meta"]
        if len(meta_tags) == 0:
            meta_tag = xml.createElement("meta")
            xml.documentElement.appendChild(meta_tag)
        else:
            meta_tag = meta_tags[0]

        # check if we have an instanceID tag
        uuid_tags = [
            n for n in meta_tag.childNodes
            if n.nodeType == Node.ELEMENT_NODE
            and n.tagName == "instanceID"]
        if len(uuid_tags) == 0:
            uuid_tag = xml.createElement("instanceID")
            meta_tag.appendChild(uuid_tag)
        else:
            uuid_tag = uuid_tags[0]
        # insert meta and instanceID
        text_node = xml.createTextNode(u"uuid:%s" % uuid)
        uuid_tag.appendChild(text_node)
        return xml.toxml()
    return xml_str


def update_mongo_for_xform(xform, only_update_missing=True):
    instance_ids = set(
        [i.id for i in Instance.objects.only('id').filter(xform=xform)])
    sys.stdout.write("Total no of instances: %d\n" % len(instance_ids))
    mongo_ids = set()
    user = xform.user
    userform_id = "%s_%s" % (user.username, xform.id_string)
    if only_update_missing:
        sys.stdout.write("Only updating missing mongo instances\n")
        mongo_ids = set(
            [rec[common_tags.ID] for rec in mongo_instances.find(
                {common_tags.USERFORM_ID: userform_id},
                {common_tags.ID: 1})])
        sys.stdout.write("Total no of mongo instances: %d\n" % len(mongo_ids))
        # get the difference
        instance_ids = instance_ids.difference(mongo_ids)
    else:
        # clear mongo records
        mongo_instances.remove({common_tags.USERFORM_ID: userform_id})
    # get instances
    sys.stdout.write(
        "Total no of instances to update: %d\n" % len(instance_ids))
    instances = Instance.objects.only('id').in_bulk(
        [id for id in instance_ids])
    total = len(instances)
    done = 0
    for id, instance in instances.items():
        (pi, created) = ParsedInstance.objects.get_or_create(instance=instance)
        pi.save(async=False)
        done += 1
        # if 1000 records are done, flush mongo
        if (done % 1000) == 0:
            sys.stdout.write(
                'Updated %d records, flushing MongoDB...\n' % done)
        settings._MONGO_CONNECTION.admin.command({'fsync': 1})
        progress = "\r%.2f %% done..." % ((float(done) / float(total)) * 100)
        sys.stdout.write(progress)
        sys.stdout.flush()
    # flush mongo again when done
    settings._MONGO_CONNECTION.admin.command({'fsync': 1})
    sys.stdout.write(
        "\nUpdated %s\n------------------------------------------\n"
        % xform.id_string)


def mongo_sync_status(remongo=False, update_all=False, user=None, xform=None):
    qs = XForm.objects.only('id_string').select_related('user')
    if user and not xform:
        qs = qs.filter(user=user)
    elif user and xform:
        qs = qs.filter(user=user, id_string=xform.id_string)
    else:
        qs = qs.all()

    total = qs.count()
    found = 0
    done = 0
    total_to_remongo = 0
    report_string = ""
    for xform in queryset_iterator(qs, 100):
        # get the count
        user = xform.user
        instance_count = Instance.objects.filter(xform=xform).count()
        userform_id = "%s_%s" % (user.username, xform.id_string)
        mongo_count = mongo_instances.find(
            {common_tags.USERFORM_ID: userform_id}).count()

        if instance_count != mongo_count or update_all:
            line = "user: %s, id_string: %s\nInstance count: %d\t"\
                   "Mongo count: %d\n---------------------------------"\
                   "-----\n" % (
                       user.username, xform.id_string, instance_count,
                       mongo_count)
            report_string += line
            found += 1
            total_to_remongo += (instance_count - mongo_count)

            # should we remongo
            if remongo or (remongo and update_all):
                if update_all:
                    sys.stdout.write(
                        "Updating all records for %s\n--------------------"
                        "---------------------------\n" % xform.id_string)
                else:
                    sys.stdout.write(
                        "Updating missing records for %s\n----------------"
                        "-------------------------------\n"
                        % xform.id_string)
                update_mongo_for_xform(
                    xform, only_update_missing=not update_all)
        done += 1
        sys.stdout.write(
            "%.2f %% done ...\r" % ((float(done) / float(total)) * 100))
    # only show stats if we are not updating mongo, the update function
    # will show progress
    if not remongo:
        line = "Total # of forms out of sync: %d\n" \
            "Total # of records to remongo: %d\n" % (
            found, total_to_remongo)
        report_string += line
    return report_string


def remove_xform(xform):
    # disconnect parsed instance pre delete signal
    pre_delete.disconnect(_remove_from_mongo, sender=ParsedInstance)

    # delete instances from mongo db
    query = {
        ParsedInstance.USERFORM_ID:
        "%s_%s" % (xform.user.username, xform.id_string)}
    xform_instances.remove(query, j=True)

    # delete xform, and all related models
    xform.delete()

    # reconnect parsed instance pre delete signal?
    pre_delete.connect(_remove_from_mongo, sender=ParsedInstance)
