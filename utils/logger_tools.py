from cStringIO import StringIO
from datetime import date
import decimal
import json
import os
from PIL import Image
import tempfile
import traceback
import urllib2 as urllib

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
from pyxform.errors import PyXFormError

from odk_logger.models import Attachment
from odk_logger.models import Instance
from odk_viewer.models import ParsedInstance
from odk_logger.models import SurveyType
from odk_logger.models import XForm
from odk_logger.models.xform import XLSFormError
from odk_logger.xform_instance_parser import InstanceParseError
from utils.viewer_tools import get_path


@transaction.commit_on_success
def create_instance(username, xml_file, media_files,
        status=u'submitted_via_web'):
    """
    I used to check if this file had been submitted already, I've
    taken this out because it was too slow. Now we're going to create
    a way for an admin to mark duplicate instances. This should
    simplify things a bit.
    """
    xml = xml_file.read()
    xml_file.close()
    user = get_object_or_404(User, username=username)
    existing_instance_count = Instance.objects.filter(xml=xml,
            user=user).count()
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

    if proceed_to_create_instance:
        instance = Instance.objects.create(xml=xml, user=user, status=status)
        for f in media_files:
            Attachment.objects.get_or_create(instance=instance, media_file=f)
        if instance.xform is not None:
            pi, created = ParsedInstance.objects.get_or_create(
                    instance=instance)
        return instance
    return None


def report_exception(subject, info, exc_info=None):
    if exc_info:
        cls, err = exc_info[:2]
        info += u"Exception in request: %s: %s" % (cls.__name__, err)
        info += u"".join(traceback.format_exception(*exc_info))

    if settings.DEBUG or settings.TESTING_MODE:
        print subject
        print info
    else:
        mail_admins(subject=subject, message=info)


def round_down_geopoint(num):
    if num:
        decimal_mult = 1000000
        return str(decimal.Decimal(int(num * decimal_mult))/decimal_mult)
    return None

def response_with_mimetype_and_name(mimetype, name, extension=None,
    show_date=True, file_path=None, use_local_filesystem=False,
    full_mime=False):
    if extension == None:
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
    response['Content-Disposition'] = disposition_ext_and_date(name, extension,
            show_date)
    return response


def disposition_ext_and_date(name, extension, show_date=True):
    if name == None:
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
            'text': 'Form with this id already exists.',
        }
    except ValidationError as e:
        # on clone invalid URL
        return {
            'type': 'alert-error',
            'text': 'Invalid URL format.',
        }
    except AttributeError as e:
        # form.publish returned None, not sure why...
        return {
            'type': 'alert-error',
            'text': unicode(e),
        }


def get_dimensions((width, height), longest_side):
    if width > height:
        width = longest_side
        height = (height/width) * longest_side
    elif height >width:
        height = longest_side
        width = (width/height) * longest_side
    else:
        height = longest_side
        width = longest_side
    return (width, height)


def _save_thumbnails(image, path, size, suffix, filename=None):
    # If filename is present, resize on s3 fs
    if filename:
        default_storage = get_storage_class()()
        fs = get_storage_class('django.core.files.storage.FileSystemStorage')()
        image.thumbnail(get_dimensions(image.size, size), Image.ANTIALIAS)
        image.save(get_path(path, suffix))

        default_storage.save(get_path(filename, suffix),
                                fs.open(get_path(path, suffix)))
    else:
        image.thumbnail(get_dimensions(image.size, size), Image.ANTIALIAS)
        image.save(get_path(path, suffix))


def resize(filename):
    default_storage = get_storage_class()()
    path = default_storage.url(filename)
    img_file = urllib.urlopen(path)
    im = StringIO(img_file.read())
    img_file.close()
    image = Image.open(im)
    conf = settings.THUMB_CONF

    fs = get_storage_class('django.core.files.storage.FileSystemStorage')()
    loc_path = fs.path(filename)

    [_save_thumbnails(image, loc_path, conf[key]['size'], conf[key]['suffix'],
                                    filename=filename) for key in conf.keys()]

def resize_local_env(filename):
    default_storage = get_storage_class()()
    path = default_storage.path(filename)
    image = Image.open(path)
    conf = settings.THUMB_CONF

    [_save_thumbnails(image, path, conf[key]['size'], conf[key]['suffix'])
                                                        for key in conf.keys()]
