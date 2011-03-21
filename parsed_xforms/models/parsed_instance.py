from django.db import models
from django.conf import settings

from xform_manager.models import XForm, Instance
from phone_manager.models import Phone
from surveyor_manager.models import Surveyor
from locations.models import District

from xform_manager import utils, tag
import sys

# this is Mongo Collection (SQL table equivalent) where we will store
# the parsed submissions
xform_instances = settings.MONGO_DB.instances

# tags that we'll be looking for
REGISTRATION = u"registration"
REGISTRATION_NAME = u"name"
PHONE_UPDATE = u"phone"
# tags we'll be adding
ID = u"_id"
SURVEYOR_NAME = u"_surveyor_name"
DISTRICT_ID = u"_district_id"
ATTACHMENTS = u"_attachments"
DATE = u"_date"

class ParsedInstance(models.Model):
    # I should rename this model, maybe Survey
    instance = models.OneToOneField(Instance, related_name="parsed_instance")
    phone = models.ForeignKey(Phone, null=True)
    surveyor = models.ForeignKey(Surveyor, null=True)
    district = models.ForeignKey(District, null=True)

    class Meta:
        app_label = "parsed_xforms"

    def _set_phone(self, doc):
        self.phone, created = Phone.objects.get_or_create(imei=doc[tag.IMEI])

    @classmethod
    def get_survey_owner(cls, parsed_instance):
        # get all registrations for this phone that happened before
        # this instance
        qs = cls.objects.filter(instance__survey_type__slug=REGISTRATION,
                                phone=parsed_instance.phone)
        #                         instance__start_time__lte=parsed_instance.instance.start_time)
        # if qs.count()>0:
        #     most_recent_registration = qs.order_by("-instance__start_time")[0]
        #     return most_recent_registration.surveyor

        # this needs to be based on the start as above
        return None if qs.count()==0 else qs[0]

    def _set_surveyor(self, doc):
        if doc[tag.INSTANCE_DOC_NAME]==REGISTRATION:
            name = doc.get(REGISTRATION_NAME, u"")
            if not name:
                raise Exception(
                    "Registration must have a non-empty name.",
                    self.instance.xml
                    )
            kwargs = {"username" : "surveyor%d" % Surveyor.objects.count(),
                      "password" : "noneisabadd3f4u1tpassword",
                      "name" : name,}
            self.surveyor = Surveyor.objects.create(**kwargs)
        else:
            # requires phone and start_time to be set
            self.surveyor = ParsedInstance.get_survey_owner(self)

    # This is a hack to fix some of the nastiness that I created in
    # the field. Hoping the next round will be a lot cleaner.
    lgas_by_state = {
        u'lga2' : 38, # Song
        u'lga15' : 296, # Kuje
        u'lga17' : 325, # Nwangele
        u'lga18' : 360, # Miga
        u'lga29' : 615, # Akoko_North_West
        }
    lgas_by_name = {
        u'Song' : 38,
        u'Kuje' : 296,
        u'Nwangele' : 325,
        u'Miga' : 360,
        u'Akoko_North_West' : 615,
        u'song' : 38,
        u'kuje' : 296,
        u'nwangele' : 325,
        u'miga' : 360,
        u'akoko_north_west' : 615,
        }
    def _set_district(self, doc):
        self.district = None
        for k in doc.keys():
            if k==u"lga" and doc[k] in self.lgas_by_name:
                self.district = District.objects.get(pk=self.lgas_by_name[doc[k]])
            elif k in self.lgas_by_state.keys():
                self.district = District.objects.get(pk=self.lgas_by_state[k])

    def get_from_mongo(self):
        result = xform_instances.find_one(self.id)
        if result: return result
        raise utils.MyError(
            "This instance hasn't been parsed into Mongo"
            )
    
    def save(self, *args, **kwargs):
        doc = self.instance.get_dict()
        
        self._set_phone(doc)
        self._set_surveyor(doc)
        self._set_district(doc)
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
    try:
        parsed_instance, created = \
            ParsedInstance.objects.get_or_create(instance=kwargs["instance"])
    except:
        # catch any exceptions and print them to the error log
        # it'd be good to add more info to these error logs
        e = sys.exc_info()[1]
        utils.report_exception(
            "problem parsing submission",
            e.__unicode__(),
            sys.exc_info()
            )
    
post_save.connect(_parse_instance, sender=Instance)
