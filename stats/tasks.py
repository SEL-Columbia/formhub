import celery
from stats.models import StatsCount


@celery.task
def stat_log(key, value):
    try:
        sc = StatsCount.objects.create(key=key, value=value)
    except ValueError:
        return None
    return sc