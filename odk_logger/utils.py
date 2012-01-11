# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

class MyError(Exception):
    pass


import traceback
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

def response_with_mimetype_and_name(_mimetype, name):
    response = HttpResponse(mimetype=("application/%s" % _mimetype))
    response['Content-Disposition'] = 'attachment; filename=%s_%s.xls' % (name, date.today().strftime("%Y_%m_%d"))
    return response

