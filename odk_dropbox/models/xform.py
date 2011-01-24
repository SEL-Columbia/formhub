#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import datetime
from django.db import models
from .. import utils, tag
from .instance import xform_instances
from district import District

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
        super(XForm, self).save(*args, **kwargs)
        # This is janky
        if XForm.objects.filter(title=self.title, active=True).count()>1:
            raise Exception("We can only have a single active form with a particular title")

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
                    #logme
                    print "variable %s does not exist in vardict" % path
                elif vardict[path][u"type"] in cleaner:
                    data[path] = cleaner[vardict[path][u"type"]](data[path])
        
        data[u'district_id'] = self.calculate_district_id(data)
        
    def calculate_district_id(self, data):
        """one way to calculate the closest district.
        data dict must be in format: "{'lat': a, 'lng': b}"
        """
        try:
            latlng = {'lat': float(data[u'geopoint'][u'latitude']), \
                    'lng': float(data[u'geopoint'][u'longitude'])}
            district_id = District.closest_district(latlng).id
        except:
            district_id = False
        return district_id

    def __unicode__(self):
        return getattr(self, "id_string", "")

    def instances(self):
        return xform_instances.find({tag.FORM_ID : self.id_string})

    def submission_count(self):
        return self.instances().count()
    submission_count.short_description = "Submission Count"

    def date_of_last_submission(self):
        newest_instance = self.instances().sort(tag.TIME_END)[0]
        if newest_instance: return newest_instance[tag.TIME_END]
        return None
