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
