from django_mongokit import get_database
db = get_database()
xform_instances = db.instances

from django.db import models
from .xform import XForm
from .phone import Phone
from .surveyor import Surveyor
from .district import District
from .. import utils, tag

class Instance(models.Model):
    # I should rename this model, maybe Survey
    xml = models.TextField()
    xform = models.ForeignKey(XForm)
    phone = models.ForeignKey(Phone)
    start_time = models.DateTimeField()
    surveyor = models.ForeignKey(Surveyor, null=True)
    district = models.ForeignKey(District, null=True)

    class Meta:
        app_label = 'odk_dropbox'

    def _set_xform(self, doc):
        self.xform = XForm.objects.get(id_string=doc[tag.XFORM_ID_STRING])

    def _set_phone(self, doc):
        self.phone, created = Phone.objects.get_or_create(
            device_id=doc[tag.DEVICE_ID]
            )

    def _set_start_time(self, doc):
        self.start_time = doc[tag.DATE_TIME_START]

    def _set_surveyor(self, doc):
        if doc[tag.INSTANCE_DOC_NAME]==tag.REGISTRATION:
            names = doc[tag.REGISTRATION_NAME].title().split()
            kwargs = {"username" : str(Surveyor.objects.all().count()),
                      "password" : "none",
                      "last_name" : names.pop(),
                      "first_name" : " ".join(names),}
            self.surveyor = Surveyor.objects.create(**kwargs)
        else:
            # I'M WORRIED ABOUT THIS IMPORT, PUTTING IT DOWN HERE TO
            # AVOID A CIRCULAR IMPORT
            from .registration import Registration
            # requires phone and start_time to be set
            self.surveyor = Registration.get_survey_owner(self)

    def _set_district(self, doc):
        # I'll do this later
        self.district = None

    def get_from_mongo(self):
        result = xform_instances.find_one(self.id)
        if result: return result
        raise Exception("This instance hasn't been parsed into Mongo")

    def save(self, *args, **kwargs):
        doc = utils.parse_xform_instance(self.xml)
        self._set_xform(doc)
        self.xform.clean_instance(doc)
        self._set_phone(doc)
        self._set_start_time(doc)
        self._set_surveyor(doc)
        self._set_district(doc)
        super(Instance, self).save(*args, **kwargs)
        doc[tag.ID] = self.id
        xform_instances.save(doc)
