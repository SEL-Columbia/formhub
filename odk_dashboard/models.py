#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import os, re, sys
from datetime import datetime
from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.conf import settings
from odk_dropbox.models import Submission
from odk_dropbox import utils

class Phone(models.Model):
    device_id = models.CharField(max_length=32)
    most_recent_surveyor = models.ForeignKey("Surveyor", null=True, blank=True)
    most_recent_number = models.CharField(max_length=32, null=True, blank=True)

    def __unicode__(self):
        return self.device_id

class GPS(models.Model):
    latitude = models.FloatField()
    longitude = models.FloatField()
    altitude = models.FloatField()
    accuracy = models.FloatField()
    
    def to_dict(self):
        return {'lat':self.latitude, 'lng':self.longitude, 'acc':self.accuracy}

class SurveyType(models.Model):
    name = models.CharField(max_length=32)

class ParsedSubmission(models.Model):
    submission = models.ForeignKey(Submission)
    survey_type = models.ForeignKey(SurveyType)
    start = models.DateTimeField()
    end = models.DateTimeField()
    gps = models.ForeignKey(GPS, null=True, blank=True)
    surveyor = models.ForeignKey("Surveyor", null=True, blank=True, related_name="submissions")
    phone = models.ForeignKey(Phone)

class Surveyor(User):
    registration = models.ForeignKey(ParsedSubmission, related_name="not_meant_to_be_used")
    # for now every new registration creates a new surveyor, we need a smart way to combine surveyors

def parse(submission):
    handler = utils.parse_submission(submission)
    d = handler.get_dict()

    # create parsed submission object
    kwargs = {"submission" : submission}
    m = re.search(r"^([a-zA-Z])", submission.form.id_string)
    survey_type, created = SurveyType.objects.get_or_create(name=m.group(1).lower())
    kwargs["survey_type"] = survey_type
    for key in ["start", "end"]:
        s = d[key]
        kwargs[key] = datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%f")
        assert kwargs[key].isoformat().startswith(s), "The datetime object we created doesn't recreate the string we're parsing."
    gps_str = d.get("geopoint","")
    if gps_str:
        values = gps_str.split(" ")
        keys = ["latitude", "longitude", "altitude", "accuracy"]
        items = zip(keys, values)
        gps = GPS.objects.create(**dict(items))
        kwargs["gps"] = gps
    phone, created = Phone.objects.get_or_create(device_id=d["device_id"])
    kwargs["phone"] = phone
    ps = ParsedSubmission.objects.create(**kwargs)

    if ps.survey_type.name=="registration":
        names = d["name"].split()
        # how are we going to merge users? I'm going to ignore that right now
        kwargs = {"username" : str(Surveyor.objects.all().count()),
                  "password" : "none",
                  "last_name" : names.pop(),
                  "first_name" : " ".join(names),
                  "registration" : ps}
        Surveyor.objects.create(**kwargs)
    ps.save()

def _parse(sender, **kwargs):
    # make sure we haven't parsed this submission before
    qs = ParsedSubmission.objects.filter(submission=kwargs["instance"])
    if qs.count()==0:
        try:
            parse(kwargs["instance"])
        except:
            # catch any exceptions and print them to the error log
            # it'd be good to add more info to these error logs
            e = sys.exc_info()[1]
            utils.report_exception(
                "problem parsing submission",
                e.__unicode__(),
                sys.exc_info()
                )

post_save.connect(_parse, sender=Submission)


