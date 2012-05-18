from datetime import date
import os
import tempfile
import traceback
from PIL import Image
import urllib2 as urllib
from PIL import Image
from cStringIO import StringIO
import json
import pyexiv2

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
from utils.geotag import set_gps_location


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

def _save_thumbnails(image, path, size, suffix, filename=None):
    # If filename is present, resize on s3 fs
    if filename:
        default_storage = get_storage_class()()
        fs = get_storage_class('django.core.files.storage.FileSystemStorage')()
        image.thumbnail(get_dimensions(image.size, size), Image.ANTIALIAS)
        image.save(get_path(path, suffix))
        
        # copy EXIF data
        source_image = pyexiv2.ImageMetadata(fs.path(filename))
        source_image.read()
        dest_image = pyexiv2.ImageMetadata(get_path(path, suffix))
        dest_image.read()
        source_image.copy(dest_image)
        
        # set EXIF image size info to resized size
        dest_image["Exif.Photo.PixelXDimension"] = image.size[0]
        dest_image["Exif.Photo.PixelYDimension"] = image.size[1]
        dest_image.write()
        
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
    image = Image.open(im)
    conf = settings.THUMB_CONF

    fs = get_storage_class('django.core.files.storage.FileSystemStorage')()
    loc_path = fs.path(filename)

    _save_thumbnails(image, loc_path, conf['large']['size'], 
                            conf['large']['suffix'], filename=filename)
    _save_thumbnails(image, loc_path, conf['medium']['size'], 
                            conf['medium']['suffix'], filename=filename)
    _save_thumbnails(image, loc_path, conf['small']['size'], 
                            conf['small']['suffix'], filename=filename)

def resize_local_env(filename):
    default_storage = get_storage_class()()
    path = default_storage.path(filename)
    image = Image.open(path)
    conf = settings.THUMB_CONF

    _save_thumbnails(image, path, conf['large']['size'], conf['large']['suffix'])
    _save_thumbnails(image, path, conf['medium']['size'], conf['medium']['suffix'])
    _save_thumbnails(image, path, conf['small']['size'], conf['small']['suffix'])


def write_exif(attachment):
    # get the geopoint fields
    types =json.loads(attachment.instance.xform.json)
    column = ''
    for x in types['children']:
        if x['type'] == 'geopoint':
            column = x['name']     
    
    d = attachment.instance.get_dict()
    gps = d.get(column, None)
    if gps:
        lat, lng, alt, acc = gps.split()
        fs = get_storage_class('django.core.files.storage.FileSystemStorage')()
        try:
            default_storage = get_storage_class()()
            if default_storage.__class__ != fs.__class__:
                path = default_storage.url(attachment.media_file.name)
                img_file = urllib.urlopen(path)
                im = StringIO(img_file.read())
                image = Image.open(im)
                image.save(fs.path(attachment.media_file.name))
                set_gps_location(fs.path(attachment.media_file.name), 
                                            float(lat), float(lng))
                default_storage.save(attachment.media_file.name, 
                                fs.open(fs.path(attachment.media_file.name)))
            else:
                path = default_storage.path(attachment.media_file.name)
                set_gps_location(path, float(lat), float(lng))
        except (IOError, OSError), e:
            print 'Error geocoding %s: %s' % (attachment.media_file.name, e)
