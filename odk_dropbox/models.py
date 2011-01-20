#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import os, re, sys
from xml.dom.minidom import parseString, Element
from django.db import models
from django.db.models.signals import pre_save
from django.conf import settings
from . import utils
import datetime

FORM_PATH = "odk/forms"
INSTANCE_PATH = "odk/instances"

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

def _recursive_clean(data, variables):
    for k in data.keys():
        if type(data[k])==dict:
            _recursive_clean(data[k], variables[k])                
        elif data[k] and cleaner[variables[k]["type"]]:
            data[k] = cleaner[variables[k]["type"]](data[k])
        elif variables[k]["type"]==u'dateTime':
            print data[k]

class XForm(models.Model):
    xml = models.TextField()
    active = models.BooleanField()
    description = models.TextField(blank=True, null=True, default="")
    id_string = models.CharField(
        unique=True, editable=False, verbose_name="ID String", max_length=64
        )
    title = models.CharField(editable=False, max_length=64)

    class Meta:
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
        _recursive_clean(data, self.parser.get_variable_dictionary())

    def __unicode__(self):
        return getattr(self, "id_string", "")

    def path(self):
        return settings.MEDIA_ROOT + self.xml_file.name

    def url(self):
        return self.xml_file.url

    def slug(self):
        return self.id_string
        return utils.sluggify(self.id_string)

    def submission_count(self):
        return self.instances.all().count()
    submission_count.short_description = "Submission Count"

    def date_of_last_submission(self):
        qs = Submission.objects.filter(instance__form=self).order_by("-posted")
        if qs.count()>0:
            return qs[0].posted



    supported_controls = ["input", "select1", "select", "upload"]

    def get_control_dict(self):
        def get_pairs(e):
            result = []
            if hasattr(e, "tagName") and e.tagName in self.supported_controls:
                result.append( (e.getAttribute("ref"),
                                get_text(follow(e, "label").childNodes)) )
            if e.hasChildNodes:
                for child in e.childNodes:
                    result.extend(get_pairs(child))
            return result
        return dict(get_pairs(self.follow("h:body")))

    def get_dictionary(self):
        d = self.get_control_dict()
        return [(get_name(b), d.get(get_nodeset(b),"")) for b in self.get_bindings()]


from couchdbkit.ext.django.schema import *

# class GPS(DocumentSchema):
#     latitude = FloatProperty()
#     longitude = FloatProperty()
#     altitude = FloatProperty()
#     accuracy = FloatProperty()

# class Location(DocumentSchema):
#     gps = SchemaProperty(GPS)
#     lga = IntegerProperty()

# class SurveyData(DocumentSchema):
#     device_id = StringProperty()
#     start = DateTimeProperty()
#     end = DateTimeProperty()
#     location = SchemaProperty(Location)
#     picture = StringProperty()

class Instance(Document):
    pass
    # form_id = StringProperty()
    # survey_type = StringProperty()
    # survey_data = SchemaProperty(SurveyData)

def make_submission(xml_file, media_files):
    """
    I used to check if this file had been submitted already, I've
    taken this out because it was too slow. Now we're going to create
    a way for an admin to mark duplicate submissions. This should
    simplify things a bit.
    """
    # add the parsed xml
    data = utils.parse_odk_xml(xml_file)

    try:
        xform = XForm.objects.get(id_string=data["form_id"])
    except XForm.DoesNotExist:
        utils.report_exception("missing form", data["form_id"])
        return None

    xform.clean_instance(data["survey_data"])

    doc = Instance(data)
        # form_id=data["form_id"],
        # survey_type=data["survey_type"],
        # survey_data=SurveyData(data["survey_data"])
        # )        
    doc.save()

    # attach all the files
    for f in [xml_file] + media_files: doc.put_attachment(f)
