#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import datetime
from django.db import models
from .. import utils, tag

# these cleaners will be used when saving data
# All cleaned types should be in this list
cleaner = {
    u'geopoint': lambda(x): dict(zip(
            ["latitude", "longitude", "altitude", "accuracy"],
            x.split()
            )),
    u'dateTime': lambda(x): datetime.datetime.strptime(
        x.split(".")[0],
        '%Y-%m-%dT%H:%M:%S'
        ),
    }

class XForm(models.Model):
    # web_title is used if the user wants to display a different title
    # on the website
    web_title = models.CharField(max_length=64)
    downloadable = models.BooleanField()
    description = models.TextField(blank=True, null=True, default="")
    xml = models.TextField()
    id_string = models.CharField(
        unique=True, editable=False, verbose_name="ID String", max_length=64
        )
    title = models.CharField(editable=False, max_length=64)

    class Meta:
        app_label = 'odk_logger'
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
        super(XForm, self).save(*args, **kwargs)

    def clean_instance(self, data):
        """
                1. variable doesn't start with _
                2. if variable doesn't exist in vardict log message
                3. if there is data and a cleaner, clean that data
        """            
        self.guarantee_parser()
        vardict = self.parser.get_variable_dictionary()
        for path in data.keys():
            if not path.startswith(u"_") and data[path]:
                if path not in vardict:
                    raise utils.MyError(
                        "The XForm %(id_string)s does not describe all "
                        "the variables seen in this instance. "
                        "Specifically, there is no definition for "
                        "%(path)s." % {
                            "id_string" : self.id_string,
                            "path" : path
                            }
                        )
                elif vardict[path][u"type"] in cleaner:
                    data[path] = cleaner[vardict[path][u"type"]](data[path])
        
        data[u'_district_id'] = self.calculate_district_id(data)
        
    def __unicode__(self):
        return getattr(self, "id_string", "")

    def submission_count(self):
        return self.surveys.count()
    submission_count.short_description = "Submission Count"

    def date_of_last_submission(self):
        qs = self.instances().sort(tag.DATE_TIME_END)
        if qs.count()==0: return None
        # return the newest instance
        return qs[0][tag.DATE_TIME_END]
