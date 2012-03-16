from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save

from .xform import XForm
from .survey_type import SurveyType
from odk_logger.xform_instance_parser import XFormInstanceParser, \
     XFORM_ID_STRING
from utils.model_tools import set_uuid


def log(*args, **kwargs):
    """
    This is a place holder for a real logging function.
    """
    pass


class Instance(models.Model):
    # I should rename this model, maybe Survey
    xml = models.TextField()
    user = models.ForeignKey(User, related_name='surveys', null=True)

    #using instances instead of surveys breaks django
    xform = models.ForeignKey(XForm, null=True, related_name="surveys")
    start_time = models.DateTimeField(null=True)
    date = models.DateField(null=True)
    survey_type = models.ForeignKey(SurveyType)

    #shows when we first received this instance
    date_created = models.DateTimeField(auto_now_add=True)
    #this will end up representing "date last parsed"
    date_modified = models.DateTimeField(auto_now=True)

    # ODK keeps track of three statuses for an instance:
    # incomplete, submitted, complete
    # we will add a fourth status: submitted_via_web
    status = models.CharField(max_length=20,
                              default=u'submitted_via_web')
    uuid = models.CharField(max_length=32, default=u'')

    class Meta:
        app_label = 'odk_logger'

    def _set_xform(self, doc):
        try:
            self.xform = XForm.objects.get(id_string=doc[XFORM_ID_STRING], user=self.user)
        except XForm.DoesNotExist:
            self.xform = None

    def get_root_node_name(self):
        self._set_parser()
        return self._parser.get_root_node_name()

    def get(self, abbreviated_xpath):
        self._set_parser()
        return self._parser.get(abbreviated_xpath)

    def _set_survey_type(self, doc):
        self.survey_type, created = \
            SurveyType.objects.get_or_create(slug=self.get_root_node_name())

    # todo: get rid of these fields
    def _set_start_time(self, doc):
        self.start_time = None

    def _set_date(self, doc):
        self.date = None

    def save(self, *args, **kwargs):
        doc = self.get_dict()
        self._set_xform(doc)
        self._set_start_time(doc)
        self._set_date(doc)
        self._set_survey_type(doc)
        set_uuid(self)
        super(Instance, self).save(*args, **kwargs)

    def _set_parser(self):
        if not hasattr(self, "_parser"):
            self._parser = XFormInstanceParser(self.xml)

    def get_dict(self, force_new=False, flat=True):
        """Return a python object representation of this instance's XML."""
        self._set_parser()
        if flat:
            return self._parser.get_flat_dict_with_attributes()
        else:
            return self._parser.to_dict()

from utils.stathat_api import stathat_count
def stathat_form_submission(sender, instance, created, **kwargs):
    if created:
       stathat_count('formhub-submissions')
post_save.connect(stathat_form_submission, sender=Instance)
