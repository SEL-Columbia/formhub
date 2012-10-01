from django.db import models
from django.db.models import Sum


class StatsManager(models.Manager):

    def count(self, key=None):
        qs = super(StatsManager, self).get_query_set()
        if key:
            qs = qs.filter(key=key)
        return qs.aggregate(Sum('value'))['value__sum']


class StatsCount(models.Model):

    class meta:
        app_label = 'stats'

    key = models.CharField(max_length=150)
    value = models.IntegerField(default=0)
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)
    objects = models.Manager()
    stats = StatsManager()