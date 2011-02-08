from django.db import models
from django.conf import settings

from .xform import XForm
from .survey_type import SurveyType
from .. import utils, tag

class Instance(models.Model):
    # I should rename this model, maybe Survey
    xml = models.TextField()
    xform = models.ForeignKey(XForm, related_name="surveys")
    start_time = models.DateTimeField()
    date = models.DateField()
    survey_type = models.ForeignKey(SurveyType)

    class Meta:
        app_label = 'odk_logger'

    def _set_xform(self, doc):
        try:
            self.xform = XForm.objects.get(id_string=doc[tag.XFORM_ID_STRING])
        except XForm.DoesNotExist:
            raise utils.MyError(
                "Missing corresponding XForm: %s" % \
                doc[tag.XFORM_ID_STRING]
                )

    def _set_survey_type(self, doc):
        self.survey_type, created = \
            SurveyType.objects.get_or_create(slug=doc[tag.INSTANCE_DOC_NAME])

    def _set_start_time(self, doc):
        self.start_time = doc[tag.DATE_TIME_START]

    def _set_date(self, doc):
        self.date = doc[tag.DATE_TIME_START].date()

    def save(self, *args, **kwargs):
        doc = utils.parse_xform_instance(self.xml)
        self._set_xform(doc)
        self.xform.clean_instance(doc)
        self._set_start_time(doc)
        self._set_date(doc)
        self._set_survey_type(doc)
        super(Instance, self).save(*args, **kwargs)
