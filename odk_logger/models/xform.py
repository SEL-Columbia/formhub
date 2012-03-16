#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.db import models
from django.db.models.query import QuerySet
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models.signals import post_save

from utils.model_tools import set_uuid

import os
import re


def upload_to(instance, filename):
    return os.path.join(
        instance.user.username,
        'xls',
        os.path.split(filename)[1])


class XLSFormError(Exception):
    pass


class XForm(models.Model):
    xls = models.FileField(upload_to=upload_to, null=True)
    json = models.TextField(default=u'')
    description = models.TextField(default=u'', null=True)
    xml = models.TextField()

    user = models.ForeignKey(User, related_name='xforms', null=True)
    shared = models.BooleanField(default=False)
    shared_data = models.BooleanField(default=False)
    downloadable = models.BooleanField(default=True)

    # the following fields are filled in automatically
    id_string = models.SlugField(
        editable=False, verbose_name="ID"
        )
    title = models.CharField(editable=False, max_length=64)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    has_start_time = models.BooleanField(default=False)
    uuid = models.CharField(max_length=32, default=u'')

    class Meta:
        app_label = 'odk_logger'
        unique_together = (("user", "id_string"),)
        verbose_name = "XForm"
        verbose_name_plural = "XForms"
        ordering = ("id_string",)
        permissions = (
            ("view_xform", "Can view associated data"),
            )

    def file_name(self):
        return self.id_string + ".xml"

    def url(self):
        return reverse(
            "download_xform",
            kwargs={
                "username": self.user.username,
                "id_string": self.id_string
                }
            )

    def data_dictionary(self):
        from odk_viewer.models import DataDictionary
        return DataDictionary.objects.get(pk=self.pk)

    def _set_id_string(self):
        text = re.sub(r"\s+", " ", self.xml)
        matches = re.findall(r'<instance>.*id="([^"]+)".*</instance>', text)
        if len(matches) != 1:
            raise XLSFormError("There should be a single id string.", text)
        self.id_string = matches[0]

    def _set_title(self):
        text = re.sub(r"\s+", " ", self.xml)
        matches = re.findall(r"<h:title>([^<]+)</h:title>", text)
        if len(matches) != 1:
            raise XLSFormError("There should be a single title.", matches)
        self.title = u"" if not matches else matches[0]

    def update(self, *args, **kwargs):
        super(XForm, self).save(*args, **kwargs)

    def save(self, *args, **kwargs):
        set_uuid(self)
        self._set_id_string()
        if getattr(settings, 'STRICT', True) and \
                not re.search(r"^[\w-]+$", self.id_string):
            raise XLSFormError("In strict mode, the XForm ID must be a valid slug and contain no spaces.")
        self._set_title()
        super(XForm, self).save(*args, **kwargs)

    def __unicode__(self):
        return getattr(self, "id_string", "")

    def submission_count(self):
        return self.surveys.count()
    submission_count.short_description = "Submission Count"

    def time_of_last_submission(self):
        if self.submission_count() > 0:
            return self.surveys.order_by("-date_created")[0].date_created

from utils.stathat_api import stathat_count
def stathat_forms_created(sender, instance, created, **kwargs):
    if created:
       stathat_count('formhub-forms-created')
post_save.connect(stathat_forms_created, sender=XForm)
