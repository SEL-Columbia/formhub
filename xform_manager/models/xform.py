#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.db import models
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import Group
from django.conf import settings
import re

from datetime import datetime

class XForm(models.Model):
    # web_title is used if the user wants to display a different title
    # on the website
    web_title = models.CharField(max_length=64, blank=True, default="")
    downloadable = models.BooleanField()
    description = models.TextField(blank=True, null=True, default="")
    groups = models.ManyToManyField(
        Group, verbose_name=_('groups'), blank=True,
        help_text=_("Each XForm is assigned to groups, only users in atleast one of this XForm's groups will be able to update this XForm.")
        )
    xml = models.TextField()
    id_string = models.SlugField(
        unique=True, editable=False, verbose_name="ID String"
        )
    title = models.CharField(editable=False, max_length=64)

    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'xform_manager'
        verbose_name = "XForm"
        verbose_name_plural = "XForms"
        ordering = ("id_string",)
        permissions = (
            ("can_view", "Can view associated data"),
            )

    def file_name(self):
        return self.id_string + ".xml"

    def url(self):
        return reverse(
            "download_xform",
            kwargs={"id_string" : self.id_string},
            )

    def _set_id_string(self):
        text = re.sub(r"\s+", " ", self.xml)
        matches = re.findall(r'<instance>.*id="([^"]+)".*</instance>', text)
        if len(matches) != 1:
            raise Exception("There should be a single id string.", matches)
        self.id_string = matches[0]

    def _set_title(self):
        text = re.sub(r"\s+", " ", self.xml)
        matches = re.findall(r"<h:title>([^<]+)</h:title>", text)
        if len(matches) != 1:
            raise Exception("There should be a single title.", matches)
        self.title = u"" if not matches else matches[0]

    def save(self, *args, **kwargs):
        self._set_id_string()
        if getattr(settings, 'STRICT', True) and \
                not re.search(r"^[\w-]+$", self.id_string):
            raise Exception("In strict mode, the XForm ID must be a valid slug and contain no spaces.")
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
