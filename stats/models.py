from django.db import models


class StatsCount(models.Model):

    class meta:
        app_label = 'stats'

    key = models.CharField(max_length=150)
    value = models.SmallIntegerField(default=0)
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)