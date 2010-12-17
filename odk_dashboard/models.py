#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import os, re, sys
from datetime import datetime

from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.conf import settings

from odk_dropbox.models import Instance
from odk_dropbox import utils


class Phone(models.Model):
    device_id = models.CharField(max_length=32)
    most_recent_surveyor = \
        models.ForeignKey("Surveyor", null=True, blank=True)

    def __unicode__(self):
        return self.device_id


class GPS(models.Model):
    latitude = models.FloatField()
    longitude = models.FloatField()
    altitude = models.FloatField()
    accuracy = models.FloatField()

    # might consider using self.__dict__
    def to_dict(self):
        return {'lat':self.latitude, 'lng':self.longitude, 'acc':self.accuracy}


class SurveyType(models.Model):
    name = models.CharField(max_length=32)


class Location(models.Model):
    name = models.CharField(max_length=32)


class ParsedInstance(models.Model):
    instance = models.ForeignKey(Instance)
    survey_type = models.ForeignKey(SurveyType)
    start = models.DateTimeField()
    end = models.DateTimeField()
    date = models.DateField()
    gps = models.ForeignKey(GPS, null=True, blank=True)
    surveyor = models.ForeignKey(
        "Surveyor", null=True, blank=True, related_name="submissions"
        )
    phone = models.ForeignKey(Phone)
    location = models.ForeignKey(Location)


# For now every new registration creates a new surveyor, we need a
# smart way to combine surveyors.
class Surveyor(User):
    registration = models.ForeignKey(
        ParsedInstance, related_name="not_meant_to_be_used"
        )

    def name(self):
        return (self.first_name + " " + self.last_name).title()


def matching_keys(d, regexp):
    """
    Return a list of all the keys in 'd' that match the passed regular
    expression.
    """
    return [k for k in d.keys() if re.search(regexp, k)]

def matching_key(d, regexp):
    """
    Make sure there's exactly one key in 'd' that matches the passed
    regular expression and return it.
    """
    l = matching_keys(d, regexp)
    assert len(l)==1, "There should be exactly one match: " + str(l)
    return l[0]

def parse(instance):
    handler = utils.parse_instance(instance)
    d = handler.get_dict()

    for k in ["start", "end", "device_id"]:
        if k not in d:
            raise Exception("Required field missing" , k)

    # create parsed instance object
    kwargs = {"instance" : instance}

    m = re.search(r"^([a-zA-Z]+)", handler.get_form_id())
    survey_type_name = m.group(1).lower()
    survey_type, created = \
        SurveyType.objects.get_or_create(name=survey_type_name)
    kwargs["survey_type"] = survey_type

    for key in ["start", "end"]:
        s = d[key]
        kwargs[key] = datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%f")
        if not kwargs[key].isoformat().startswith(s):
            utils.report_exception(
                "datetime object doesn't recreate original string",
                "orginal: %(original)s datetime object: %(parsed)s" %
                {"original" : s, "parsed" : kwargs[key].isoformat()}
                )
    kwargs["date"] = kwargs["end"].date()

    gps_str = d.get("geopoint","")
    if gps_str:
        values = gps_str.split(" ")
        keys = ["latitude", "longitude", "altitude", "accuracy"]
        items = zip(keys, values)
        gps = GPS.objects.create(**dict(items))
        kwargs["gps"] = gps

    phone, created = \
        Phone.objects.get_or_create(device_id=d["device_id"])
    kwargs["phone"] = phone

    lga = matching_key(d, r"^lga")
    location, created = Location.objects.get_or_create(name=d[lga])
    kwargs["location"] = location

    ps = ParsedInstance.objects.create(**kwargs)

    if ps.survey_type.name=="registration":
        names = d["name"].split()
        kwargs = {"username" : str(Surveyor.objects.all().count()),
                  "password" : "none",
                  "last_name" : names.pop(),
                  "first_name" : " ".join(names),
                  "registration" : ps}
        surveyor = Surveyor.objects.create(**kwargs)
        phone.most_recent_surveyor = surveyor
        phone.save()
    ps.save()


def _parse(sender, **kwargs):
    # make sure we haven't parsed this instance before
    qs = ParsedInstance.objects.filter(instance=kwargs["instance"])
    if qs.count()==0:
        try:
            parse(kwargs["instance"])
        except:
            # catch any exceptions and print them to the error log
            # it'd be good to add more info to these error logs
            e = sys.exc_info()[1]
            utils.report_exception(
                "problem parsing instance",
                e.__unicode__(),
                sys.exc_info()
                )

post_save.connect(_parse, sender=Instance)
