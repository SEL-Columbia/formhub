from django.db import models
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from xform_manager.models import XForm, Instance
from phone_manager.models import Phone
from surveyor_manager.models import Surveyor
from locations.models import District

from xform_manager import utils
from common_tags import IMEI, DATE_TIME_START, DATE_TIME_END
import sys
import django.dispatch
import datetime

# this is Mongo Collection (SQL table equivalent) where we will store
# the parsed submissions
xform_instances = settings.MONGO_DB.instances

# tags we'll be adding
ID = u"_id"
SURVEYOR_NAME = u"_surveyor_name"
DISTRICT_ID = u"_district_id"
ATTACHMENTS = u"_attachments"
DATE = u"_date"

from nga_districts import models as nga_models

def datetime_from_str(text):
    # Assumes text looks like 2011-01-01T09:50:06.966
    date_time_str = text.split(".")[0]
    return datetime.datetime.strptime(
        date_time_str, '%Y-%m-%dT%H:%M:%S'
        )

class ParsedInstance(models.Model):
    instance = models.OneToOneField(Instance, related_name="parsed_instance")
    phone = models.ForeignKey(Phone, null=True)
    surveyor = models.ForeignKey(Surveyor, null=True)
    
    # district is no longer used except in old data. once
    # we've migrated phase I surveys, we should delete this field.
    district = models.ForeignKey(District, null=True)
    
    lga = models.ForeignKey(nga_models.LGA, null=True)
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)
    district = models.ForeignKey(District, null=True)
    surveyor = models.ForeignKey(Surveyor, null=True)
    
    class Meta:
        app_label = "parsed_xforms"
    
    def to_dict(self):
        return self.instance.get_dict()

    def _set_phone(self):
        doc = self.to_dict()
        # I'm using two different keys here because I switched the key
        # we're using in Phase II. Ideally, we'd do this using a data
        # dictionary.
        imei = doc.get(u"device_id", doc.get(u"imei", None))
        if imei:
            self.phone, created = Phone.objects.get_or_create(imei=imei)
        else:
            self.phone = None

    def _set_start_time(self):
        doc = self.to_dict()
        u_start_time = doc.get(DATE_TIME_START, u"")
        self.start_time = None if not u_start_time else \
            datetime_from_str(u_start_time)

    def _set_end_time(self):
        doc = self.to_dict()
        u_end_time = doc.get(DATE_TIME_END, u"")
        self.end_time = None if not u_end_time else \
            datetime_from_str(u_end_time)

    def _set_lga(self):
        doc = self.to_dict()
        
        zone_slug = doc.get(u'location/zone', None)
        if not zone_slug: return None
        
        state_slug = doc.get(u'location/state_in_%s' % zone_slug, None)
        if not state_slug: return None
        
        lga_slug = doc.get(u'location/lga_in_%s' % state_slug, None)
        if not lga_slug: return None
        
        try:
            state = nga_models.State.objects.get(slug=state_slug)
            self.lga = state.lgas.get(slug=lga_slug)
        except ObjectDoesNotExist, e:
            return None
    
    time_to_set_surveyor = django.dispatch.Signal()
    def _set_surveyor(self):
        self.time_to_set_surveyor.send(sender=self)
    
    def get_from_mongo(self):
        result = xform_instances.find_one(self.id)
        if result: return result
        raise utils.MyError(
            "This instance hasn't been parsed into Mongo"
            )
    
    def save(self, *args, **kwargs):
        doc = self.to_dict()
        self._set_phone()
        self._set_start_time()
        self._set_end_time()
        self._set_lga()
        self._set_surveyor()
        super(ParsedInstance, self).save(*args, **kwargs)
        doc.update(
            {
                ID : self.id,
                SURVEYOR_NAME :
                    None if not self.surveyor else self.surveyor.name,
                DISTRICT_ID :
                    None if not self.district else self.district.id,
                ATTACHMENTS :
                    [a.attachment.name for a in self.instance.attachments.all()],
                }
            )
        xform_instances.save(doc)

# http://docs.djangoproject.com/en/dev/topics/db/models/#overriding-model-methods
from django.db.models.signals import pre_delete
def _remove_from_mongo(sender, **kwargs):
    xform_instances.remove(kwargs["instance"].id)

pre_delete.connect(_remove_from_mongo, sender=Instance)

import sys

from django.db.models.signals import post_save
def _parse_instance(sender, **kwargs):
    parsed_instance, created = \
        ParsedInstance.objects.get_or_create(instance=kwargs["instance"])
    # try:
    #     parsed_instance, created = \
    #         ParsedInstance.objects.get_or_create(instance=kwargs["instance"])
    # except:
    #     # catch any exceptions and print them to the error log
    #     # it'd be good to add more info to these error logs
    #     e = sys.exc_info()[1]
    #     utils.report_exception(
    #         "problem parsing submission",
    #         e.__unicode__(),
    #         sys.exc_info()
    #         )
    
post_save.connect(_parse_instance, sender=Instance)
