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

from treebeard.mp_tree import MP_Node
import math

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
    district = models.ForeignKey("District", null=True, blank=True)

    # might consider using self.__dict__
    def to_dict(self):
        return {'lat':self.latitude, 'lng':self.longitude, \
                'acc':self.accuracy, 'district_id': self.district.id }
    
    def closest_district(self):
        districts = District.objects.filter(active=True)
        min_val = None
        district = None
        for x in range(len(districts)):
            if not district:
                district = districts[x]
                min_val = districts[x].ll_diff(self)
            else:
                mv = districts[x].ll_diff(self)
                if min_val > mv:
                    min_val = mv
                    district = districts[x]
        return district

    def save(self, *args, **kwargs):
        self.district = self.closest_district()
        super(GPS, self).save(*args, **kwargs)

class District(MP_Node):
    name = models.CharField(max_length=50)
    node_order_by = ['name']
    nickname = models.CharField(max_length=50)
    kml_present = models.BooleanField()
    active = models.BooleanField()
    latlng_string = models.CharField(max_length=50)
#    gps = models.ForeignKey(GPS, null=True, blank=True)
    
    def ll_diff(self, gps):
        ll = self.latlng()
        lat_delta = ll['lat'] - gps.latitude
        lng_delta = ll['lng'] - gps.longitude
        return float(math.fabs(lat_delta) + math.fabs(lng_delta))
    
    def latlng(self):
        try:
            lat, lng = self.latlng_string.split(",")
            o = {'lat': float(lat), 'lng': float(lng) }
        except:
            o = None
        
        return o
        
    def kml_uri(self):
        if not self.kml_present:
            return None
        else:
            return "%skml/%d.kml" % (settings.MEDIA_URL, self.id)
    
    def to_dict(self):
        return {'name':self.name, 'state':self.get_parent().name, \
                'coords':self.latlng_string, 'kml':self.kml_uri(), \
                'id':self.id }

class SurveyType(models.Model):
    name = models.CharField(max_length=32)

    def __unicode__(self):
        return self.name

class Location(models.Model):
    name = models.CharField(max_length=32)
    gps = models.ForeignKey(GPS, null=True, blank=True)

class ParsedInstance(models.Model):
    instance = models.OneToOneField(Instance)
    survey_type = models.ForeignKey(SurveyType)
    start = models.DateTimeField()
    end = models.DateTimeField()
    date = models.DateField()
    surveyor = models.ForeignKey(
        "Surveyor", null=True, blank=True, related_name="submissions"
        )
    phone = models.ForeignKey(Phone)
    location = models.ForeignKey(Location, null=True, blank=True)

    def survey_length(self):
        return self.end - self.start
        
    def surveyor_identifier(self):
        try:
            ident = self.phone.most_recent_surveyor.name()
        except:
            ident = self.phone.device_id
        return ident
    
    def title(self):
        return "Title: %s" % self.survey_type.name
    
    def to_dict(self):
        try:
            gps = self.location.gps.to_dict()
        except:
            gps = False
        
        return {'images':[x.image.url for x in self.instance.images.all()], \
                'phone': self.phone.__unicode__(), \
                'surveyor': self.surveyor_identifier(), \
                'datetime': self.end.strftime("%Y-%m-%d %H:%M"), \
                'survey_type': self.survey_type.name, \
                'gps': gps, 'id': self.id, 'title': self.title() }

# For now every new registration creates a new surveyor, we need a
# smart way to combine surveyors.
class Surveyor(User):
    registration = models.ForeignKey(
        ParsedInstance, related_name="surveyor registration"
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
    if len(l)==1:
        return l[0]
    elif len(l)==0:
        return ""
    else:
        raise Exception("There should be at most one match", l)

def starts_with(x,y):
    if len(x) < len(y):
        return y.startswith(x)
    return x.startswith(y)

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
        if not starts_with(kwargs[key].isoformat(), s):
            utils.report_exception(
                "datetime object doesn't recreate original string",
                "orginal: %(original)s datetime object: %(parsed)s" %
                {"original" : s, "parsed" : kwargs[key].isoformat()}
                )
    kwargs["date"] = kwargs["end"].date()

    lga = matching_key(d, r"^lga\d*$")
    if lga:
        gps_str = d.get("geopoint","")
        gps = None
        if gps_str:
            values = gps_str.split(" ")
            keys = ["latitude", "longitude", "altitude", "accuracy"]
            items = zip(keys, values)
            gps, created = GPS.objects.get_or_create(**dict(items))
        location, created = Location.objects.get_or_create(
            name=d[lga], gps=gps
            )
        kwargs["location"] = location

    phone, created = \
        Phone.objects.get_or_create(device_id=d["device_id"])
    kwargs["phone"] = phone

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
