from django.db import models
from django.conf import settings

from xform_manager.models import XForm, Instance
from xform_manager.views import log_error
from phone_manager.models import Phone
from surveyor_manager.models import Surveyor
from nga_districts.models import LGA

from xform_manager import utils
from common_tags import IMEI, DEVICE_ID, START_TIME, START, \
    END_TIME, END, LGA_ID, ID, SURVEYOR_NAME, ATTACHMENTS, DATE, SURVEY_TYPE
import django.dispatch
import datetime

class ParseError(Exception):
    pass

def datetime_from_str(text):
    # Assumes text looks like 2011-01-01T09:50:06.966
    if text is None: return None
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
    lga = models.ForeignKey(LGA, null=True)
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)
    surveyor = models.ForeignKey(Surveyor, null=True)
    is_new = models.BooleanField(default=False)
    
    class Meta:
        app_label = "parsed_xforms"
    
    def to_dict(self):
        if not hasattr(self, "_dict_cache"):
            self._dict_cache = self.instance.get_dict()
        self._dict_cache.update(
            {
                ID : self.instance.id,
                SURVEYOR_NAME :
                    None if not self.surveyor else self.surveyor.name,
                LGA_ID :
                    None if not self.lga else self.lga.id,
                SURVEY_TYPE: self.instance.survey_type.slug,
                ATTACHMENTS :
                    [a.media_file.name for a in self.instance.attachments.all()],
                u"_status" : self.instance.status,
                }
            )
        for mod in self.instance.modifications.all():
            self._dict_cache = mod.process_doc(self._dict_cache)
        return self._dict_cache
    
    def _set_phone(self):
        doc = self.to_dict()
        # I'm using two different keys here because I switched the key
        # we're using in Phase II. Ideally, we'd do this using a data
        # dictionary.
        if (IMEI in doc) or (DEVICE_ID in doc):
            imei = doc.get(IMEI, doc.get(DEVICE_ID))
            if imei is None:
                self.phone = None
            else:
                self.phone, created = Phone.objects.get_or_create(imei=imei)

    def _set_start_time(self):
        doc = self.to_dict()
        if START_TIME in doc:
            date_time_str = doc[START_TIME]
            self.start_time = datetime_from_str(date_time_str)
        elif START in doc:
            date_time_str = doc[START]
            self.start_time = datetime_from_str(date_time_str)
        else:
            self.start_time = None

    def _set_end_time(self):
        doc = self.to_dict()
        if END_TIME in doc:
            date_time_str = doc[END_TIME]
            self.end_time = datetime_from_str(date_time_str)
        elif END in doc:
            date_time_str = doc[END]
            self.end_time = datetime_from_str(date_time_str)
        else:
            self.end_time = None

    def _set_lga(self):
        doc = self.to_dict()

        zone_slug = doc.get(u'location/zone', None)
        if zone_slug is None: return
        state_slug = doc.get(u'location/state_in_%s' % zone_slug, None)
        if state_slug is None: return
        lga_slug = doc.get(u'location/lga_in_%s' % state_slug, None)
        if lga_slug is None: return

        try:
            self.lga = LGA.objects.get(slug=lga_slug, state__slug=state_slug)
        except LGA.DoesNotExist:
            message = "There is no LGA with (state_slug, lga_slug)="
            message += "(%(state)s, %(lga)s)" % {
                "state" : state_slug, "lga" : lga_slug}
            log_error(message)
    
    time_to_set_surveyor = django.dispatch.Signal()
    def _set_surveyor(self):
        self.time_to_set_surveyor.send(sender=self)
    
    def parse(self):
        self._set_phone()
        self._set_start_time()
        self._set_end_time()
        self._set_lga()
        self._set_surveyor()

