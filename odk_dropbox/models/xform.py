#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import datetime
from django.db import models
from .. import utils, tag
from .instance import odk_instances

# these cleaners will be used when saving data
cleaner = {
    u'binary': None,
    u'string': None,
    u'int': None,
    u'geopoint': lambda(x): dict(zip(
            ["latitude", "longitude", "altitude", "accuracy"],
            x.split()
            )),
    u'dateTime': lambda(x): datetime.datetime.strptime(
        x.split(".")[0],
        '%Y-%m-%dT%H:%M:%S'
        ),
    u'select1': None,
    u'select': None,
    }

class XForm(models.Model):
    xml = models.TextField()
    active = models.BooleanField()
    description = models.TextField(blank=True, null=True, default="")
    id_string = models.CharField(
        unique=True, editable=False, verbose_name="ID String", max_length=64
        )
    title = models.CharField(editable=False, max_length=64)

    class Meta:
        app_label = 'odk_dropbox'
        verbose_name = "XForm"
        verbose_name_plural = "XForms"
        ordering = ("id_string",)

    def guarantee_parser(self):
        # there must be a better way than this solution
        if not hasattr(self, "parser"):
            self.parser = utils.XFormParser(self.xml)

    def save(self, *args, **kwargs):
        self.guarantee_parser()
        self.id_string = self.parser.get_id_string()
        self.title = self.parser.get_title()
        if XForm.objects.filter(title=self.title, active=True).count()>0:
            raise Exception("We can only have a single active form with a particular title")
        super(XForm, self).save(*args, **kwargs)

    def clean_instance(self, data):
        self.guarantee_parser()
        vardict = self.parser.get_variable_dictionary()
        for path in data.keys():
            if not path.startswith(u"_") and data[path] and cleaner[vardict[path][u"type"]]:
                data[path] = cleaner[vardict[path][u"type"]](data[path])

    def __unicode__(self):
        return getattr(self, "id_string", "")

    def instances(self):
        return odk_instances.find({tag.FORM_ID : self.id_string})

    def submission_count(self):
        return self.instances().count()
    submission_count.short_description = "Submission Count"

    def date_of_last_submission(self):
        newest_instance = self.instances().sort(tag.TIME_END)[0]
        if newest_instance: return newest_instance[tag.TIME_END]
        return None
