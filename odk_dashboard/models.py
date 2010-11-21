from datetime import datetime
from django.db import models
from django.db.models.signals import post_save
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

def parse(submission):
    handler = utils.parse_submission(submission)
    d = handler.get_dict()
    keys = d.keys()
    assert len(keys)==1, "There should be a single root node."
    d = d[keys[0]]

    # create parsed submission object
    kwargs = {"submission" : submission,
              "survey_type" : keys[0]}
    kwargs["device_id"] = d.pop("device_id")
    kwargs["phone_number"] = d.pop("phone_number","")
    for key in ["start", "end"]:
        s = d.pop(key)
        kwargs[key] = datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%f")
        assert kwargs[key].isoformat().startswith(s), "The datetime object we created doesn't recreate the string we're parsing."
    s = d.pop("geopoint","")
    if s:
        values = s.split(" ")
        keys = ["latitude", "longitude", "altitude", "accuracy"]
        items = zip(keys, values)
        gps = GPS.objects.create(**dict(items))
        kwargs["gps"] = gps
    ps = ParsedSubmission.objects.create(**kwargs)

def _parse(sender, **kwargs):
    if kwargs["created"]:
        pass
    parse(kwargs["instance"])

post_save.connect(_parse, sender=Submission)
