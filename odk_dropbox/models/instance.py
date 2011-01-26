from django_mongokit import get_database
db = get_database()
xform_instances = db.instances

from django.db import models
from .xform import XForm
from .phone import Phone
from .surveyor import Surveyor
from .district import District
from .survey_type import SurveyType
from .. import utils, tag

class Instance(models.Model):
    # I should rename this model, maybe Survey
    xml = models.TextField()
    xform = models.ForeignKey(XForm)
    phone = models.ForeignKey(Phone)
    start_time = models.DateTimeField()
    surveyor = models.ForeignKey(Surveyor, null=True)
    district = models.ForeignKey(District, null=True)
    survey_type = models.ForeignKey(SurveyType)

    class Meta:
        app_label = 'odk_dropbox'

    def _set_xform(self, doc):
        self.xform = XForm.objects.get(id_string=doc[tag.XFORM_ID_STRING])

    def _set_phone(self, doc):
        self.phone, created = Phone.objects.get_or_create(
            device_id=doc[tag.DEVICE_ID]
            )

    def _set_survey_type(self, doc):
        self.survey_type, created = \
            SurveyType.objects.get_or_create(slug=doc[tag.INSTANCE_DOC_NAME])

    def _set_start_time(self, doc):
        self.start_time = doc[tag.DATE_TIME_START]

    @classmethod
    def get_survey_owner(cls, instance):
        # get all registrations for this phone that happened before
        # this instance
        qs = cls.objects.filter(survey_type__slug=tag.REGISTRATION,
                                phone=instance.phone,
                                start_time__lte=instance.start_time)
        if qs.count()>0:
            most_recent_registration = qs.order_by("-start_time")[0]
            return most_recent_registration.surveyor
        return None

    def _set_surveyor(self, doc):
        print doc[tag.INSTANCE_DOC_NAME]
        if doc[tag.INSTANCE_DOC_NAME]==tag.REGISTRATION:
            names = doc[tag.REGISTRATION_NAME].title().split()
            kwargs = {"username" : str(Surveyor.objects.all().count()),
                      "password" : "none",
                      "last_name" : names.pop(),
                      "first_name" : " ".join(names),}
            self.surveyor = Surveyor.objects.create(**kwargs)
        else:
            # requires phone and start_time to be set
            self.surveyor = Instance.get_survey_owner(self)

    def _set_district(self, doc):
        # I'll do this later
        self.district = None

    def get_from_mongo(self):
        result = xform_instances.find_one(self.id)
        if result: return result
        raise utils.MyError(
            "This instance hasn't been parsed into Mongo"
            )

    def save(self, *args, **kwargs):
        doc = utils.parse_xform_instance(self.xml)
        self._set_xform(doc)
        self.xform.clean_instance(doc)
        self._set_phone(doc)
        self._set_start_time(doc)
        self._set_survey_type(doc)
        self._set_surveyor(doc)
        self._set_district(doc)
        super(Instance, self).save(*args, **kwargs)
        doc[tag.ID] = self.id
        xform_instances.save(doc)
