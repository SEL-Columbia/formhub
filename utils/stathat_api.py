from django.conf import settings
from stathat import StatHat


def stathat_count(stat, count=1):
    if hasattr(settings, 'STATHAT_EMAIL'):
        stathat = StatHat()
        return stathat.ez_post_count(settings.STATHAT_EMAIL, stat, count)
