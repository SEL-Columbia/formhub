#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.db import models

class Phone(models.Model):
    device_id = models.CharField(max_length=32)
    most_recent_surveyor = \
        models.ForeignKey("Surveyor", null=True, blank=True)

    class Meta:
        app_label = 'odk_dropbox'

    def __unicode__(self):
        return self.device_id
