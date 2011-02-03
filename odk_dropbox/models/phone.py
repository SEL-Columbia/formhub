#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

from django.db import models

from .surveyor import Surveyor


class Phone(models.Model):
    """
        A phone device and it's current state on the field.
    """

    STATUS_CHOICES = (('functional', 'Functional'), 
                      ('broken', 'Broken'))

    imei = models.CharField(max_length=32, unique=True, verbose_name='IMEI')
    
    status = models.CharField(max_length=16, choices=STATUS_CHOICES,
                             default='functional', verbose_name='Status')
                             
    note = models.TextField(blank=True, null=True, verbose_name="Notes")
    
    # todo: replace this with a code field ?
    visible_id = models.CharField(max_length=32, unique=True, 
                                  verbose_name="Visible ID")
    
    # todo: checks on the phone number consistency ?
    phone_number = models.CharField(max_length=16, unique=True, 
                                    verbose_name="Current phone number")
    
    surveyor = models.ForeignKey(Surveyor,  verbose_name="Surveyor")

    class Meta:
        app_label = 'odk_dropbox'

    def __unicode__(self):
        return self.imei
