#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import os, sys
from datetime import datetime
from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.conf import settings
from odk_dropbox.models import Submission
from odk_dropbox import utils
     
class GPS(models.Model):
    latitude = models.FloatField()
    longitude = models.FloatField()
    altitude = models.FloatField()
    accuracy = models.FloatField()

class ParsedSubmission(models.Model):
    submission = models.ForeignKey(Submission)
    survey_type = models.CharField(max_length=32)
    device_id = models.CharField(max_length=32)
    phone_number = models.CharField(max_length=32, null=True, blank=True)
    start = models.DateTimeField()
    end = models.DateTimeField()
    gps = models.ForeignKey(GPS, null=True, blank=True)

class Surveyor(User):
    registration = models.ForeignKey(ParsedSubmission)

def parse(submission):
    handler = utils.parse_submission(submission)
    d = handler.get_dict()
    keys = d.keys()
    assert len(keys)==1, "There should be a single root node."
    d = d[keys[0]]

    # create parsed submission object
    kwargs = {"submission" : submission,
              "survey_type" : keys[0]}
    kwargs["device_id"] = d["device_id"]
    kwargs["phone_number"] = d.get("phone_number","")
    for key in ["start", "end"]:
        s = d[key]
        kwargs[key] = datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%f")
        assert kwargs[key].isoformat().startswith(s), "The datetime object we created doesn't recreate the string we're parsing."
    s = d.get("geopoint","")
    if s:
        values = s.split(" ")
        keys = ["latitude", "longitude", "altitude", "accuracy"]
        items = zip(keys, values)
        gps = GPS.objects.create(**dict(items))
        kwargs["gps"] = gps
    ps = ParsedSubmission.objects.create(**kwargs)

    if ps.survey_type=="registration":
        names = d["name"].split()
        kwargs = {"username" : d["device_id"],
                  "password" : "none",
                  "last_name" : names.pop(),
                  "first_name" : " ".join(names),
                  "registration" : ps}
        Surveyor.objects.create(**kwargs)
                  

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
            f = open(os.path.join(settings.PROJECT_ROOT, "error.log"), "a")
            f.write(e.__unicode__())
            f.close()

post_save.connect(_parse, sender=Submission)


