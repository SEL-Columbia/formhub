#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.db import models

from .surveyor import Surveyor


class Phone(models.Model):
    """
        A phone device and it's current state on the field.
    """

    STATUS_CHOICES = (('functional', 'Functional'), 
                      ('broken', 'Broken'))

    imei = models.CharField(max_length=32, unique=True)
    
    status = models.CharField(max_length=16, choices=STATUS_CHOICES,
                             default='functional')
                             
    note = models.TextField(blank=True, null=True)
    
    # todo: replace this with a code field ?
    visible_id = models.CharField(max_length=32, unique=True)
    
    # todo: checks on the phone number consistency ?
    phone_number = models.CharField(max_length=16, unique=True)
    
    #surveyor = models.ForeignKey(Surveyor)

    class Meta:
        app_label = 'odk_dropbox'

    def __unicode__(self):
        return self.imei
