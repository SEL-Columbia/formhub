import traceback
import tempfile
from django.conf import settings
from django.core.mail import mail_admins

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

from datetime import date
from django.http import HttpResponse
from django.core.servers.basehttp import FileWrapper
from django.core.files.storage import get_storage_class
import os

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
