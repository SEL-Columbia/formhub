from datetime import date
import os
import tempfile
import traceback
from PIL import Image
import urllib2 as urllib
from PIL import Image
from cStringIO import StringIO

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import get_storage_class
from django.core.mail import mail_admins
from django.core.servers.basehttp import FileWrapper
from django.db import IntegrityError
from django.http import HttpResponse
from odk_logger.models.xform import XLSFormError
from utils.viewer_tools import get_path
from pyxform.errors import PyXFormError


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

import decimal

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
    response['Content-Disposition'] = disposition_ext_and_date(name, extension, show_date)
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

def resize(filename):
    default_storage = get_storage_class()()
    path = default_storage.url(filename)
    img_file = urllib.urlopen(path)
    im = StringIO(img_file.read())
    image = Image.open(im)

    fs = get_storage_class('django.core.files.storage.FileSystemStorage')()
    loc_file_name = fs.path(filename)

    # Save large thumbnail
    image.thumbnail(get_dimensions(image.size, 1280), Image.ANTIALIAS)
    image.save(get_path(loc_file_name, '-lrg.'))
    default_storage.save(get_path(filename, '-lrg.'), fs.open(get_path(loc_file_name, '-lrg.')))
    
    # Then save medium thumbnail
    image.thumbnail(get_dimensions(image.size, 640), Image.ANTIALIAS)
    image.save(get_path(loc_file_name, '-med.'))
    default_storage.save(get_path(filename, '-med.'), fs.open(get_path(loc_file_name, '-med.')))

    # Then save small thumbnail
    image.thumbnail(get_dimensions(image.size, 240), Image.ANTIALIAS)
    image.save(get_path(loc_file_name, '-sml.'))
    default_storage.save(get_path(filename, '-sml.'), fs.open(get_path(loc_file_name, '-sml.')))
    
def resize_local_env(filename):
    default_storage = get_storage_class()()
    path = default_storage.path(filename)
    image = Image.open(path)

    # Save large thumbnail
    image.thumbnail(get_dimensions(image.size, 1280), Image.ANTIALIAS)
    image.save(get_path(path, '-lrg.'))

    # Then save medium thumbnail
    image.thumbnail(get_dimensions(image.size, 640), Image.ANTIALIAS)
    image.save(get_path(path, '-med.'))

    # Then save small thumbnail
    image.thumbnail(get_dimensions(image.size, 240), Image.ANTIALIAS)
    image.save(get_path(path, '-sml.'))
