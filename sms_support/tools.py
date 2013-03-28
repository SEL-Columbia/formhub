#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import mimetypes
import io
from xml.parsers.expat import ExpatError

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from django.http import HttpRequest

from utils.logger_tools import create_instance
from odk_logger.xform_instance_parser import (InstanceEmptyError,
                                              InstanceInvalidUserError,
                                              IsNotCrowdformError,
                                              DuplicateInstance)
from odk_logger.models.instance import FormInactiveError
from odk_logger.models import XForm
from utils.log import audit_log, Actions


SMS_API_ERROR = 'SMS_API_ERROR'
SMS_PARSING_ERROR = 'SMS_PARSING_ERROR'
SMS_SUBMISSION_ACCEPTED = 'SMS_SUBMISSION_ACCEPTED'
SMS_SUBMISSION_REFUSED = 'SMS_SUBMISSION_REFUSED'
SMS_INTERNAL_ERROR = 'SMS_INTERNAL_ERROR'


def sms_media_to_file(file_object, name):
    if isinstance(file_object, basestring):
        file_object = io.BytesIO(file_object)

    def getsize(f):
        f.seek(0)
        f.read()
        s = f.tell()
        f.seek(0)
        return s

    name = name.strip()
    content_type, charset = mimetypes.guess_type(name)
    size = getsize(file_object)
    return InMemoryUploadedFile(file=file_object, name=name,
                                field_name=None, content_type=content_type,
                                charset=charset, size=size)


def generate_instance(username, xml_file, media_files, uuid=None):
    ''' Process an XForm submission as if done via HTTP

        :param IO xml_file: file-like object containing XML XForm
        :param string username: username of the Form's owner
        :param list media_files: a list of UploadedFile objects
        :param string uuid: an optionnal uuid for the instance.

        :returns a (status, message) tuple. '''

    try:
        instance = create_instance(
            username,
            xml_file,
            media_files,
            uuid=uuid
        )
    except InstanceInvalidUserError:
        return (SMS_SUBMISSION_REFUSED, _(u"Username or ID required."))
    except IsNotCrowdformError:
        return (SMS_SUBMISSION_REFUSED,
                _(u"Sorry but the crowd form you submitted to is closed."))
    except InstanceEmptyError:
        return (SMS_INTERNAL_ERROR,
                _(u"Received empty submission. No instance was created"))
    except FormInactiveError:
        return (SMS_SUBMISSION_REFUSED, _(u"Form is not active"))
    except XForm.DoesNotExist:
        return (SMS_SUBMISSION_REFUSED,
                _(u"Form does not exist on this account"))
    except ExpatError:
        return (SMS_INTERNAL_ERROR, _(u"Improperly formatted XML."))
    except DuplicateInstance:
        return (SMS_SUBMISSION_REFUSED, _(u"Duplicate submission"))

    if instance is None:
        return (SMS_INTERNAL_ERROR,
                _(u"Unable to create submission."))

    user = User.objects.get(username=username)

    audit = {
        "xform": instance.xform.id_string
    }
    audit_log(Actions.SUBMISSION_CREATED,
              user, instance.xform.user,
              _("Created submission on form %(id_string)s.") %
              {"id_string": instance.xform.id_string}, audit, HttpRequest())

    xml_file.close()
    if len(media_files):
        [_file.close() for _file in media_files]

    return (SMS_SUBMISSION_ACCEPTED, _(u"Success"))
