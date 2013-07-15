from django.conf import settings
from stathat import StatHat
from urllib2 import HTTPError
from django.core.mail import mail_admins


def stathat_count(stat, count=1):
    if hasattr(settings, 'STATHAT_EMAIL'):
        stathat = StatHat()

        try:
            result = stathat.ez_post_count(settings.STATHAT_EMAIL, stat, count)
        except HTTPError as e:
            mail_admins("StatHat API Error", e.message)
            return False
        else:
            return result

