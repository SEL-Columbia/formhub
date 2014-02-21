import re
from django.db import models
from django.db.models.signals import post_save
from django.db.models.signals import post_delete
from django.contrib.auth.models import User
from django.utils import timezone
from .xform import XForm
from .survey_type import SurveyType
from odk_logger.xform_instance_parser import XFormInstanceParser, \
    clean_and_parse_xml, get_uuid_from_xml
from utils.model_tools import set_uuid
from django.utils.translation import ugettext as _
from taggit.managers import TaggableManager


class FormInactiveError(Exception):
    def __unicode__(self):
        return _("Form is inactive")

    def __str__(self):
        return unicode(self).encode('utf-8')


# need to establish id_string of the xform before we run get_dict since
# we now rely on data dictionary to parse the xml
def get_id_string_from_xml_str(xml_str):
    xml_obj = clean_and_parse_xml(xml_str)
    root_node = xml_obj.documentElement
    return root_node.getAttribute(u"id")


class Instance(models.Model):
    # I should rename this model, maybe Survey
    xml = models.TextField()
    user = models.ForeignKey(User, related_name='surveys', null=True)

    # using instances instead of surveys breaks django
    xform = models.ForeignKey(XForm, null=True, related_name='surveys')
    start_time = models.DateTimeField(null=True)
    date = models.DateField(null=True)
    survey_type = models.ForeignKey(SurveyType)

    # shows when we first received this instance
    date_created = models.DateTimeField(auto_now_add=True)

    # this will end up representing "date last parsed"
    date_modified = models.DateTimeField(auto_now=True)

    # this will end up representing "date instance was deleted"
    deleted_at = models.DateTimeField(null=True, default=None)
    is_deleted = models.BooleanField(null=False, default=False)

    # ODK keeps track of three statuses for an instance:
    # incomplete, submitted, complete
    # we will add a fourth status: submitted_via_web
    status = models.CharField(max_length=20,
                              default=u'submitted_via_web')
    uuid = models.CharField(max_length=249, default=u'')

    tags = TaggableManager()

    class Meta:
        app_label = 'odk_logger'

    def _set_xform(self, id_string):
        self.xform = XForm.objects.get(
            id_string=id_string, user=self.user)

    def get_root_node_name(self):
        self._set_parser()
        return self._parser.get_root_node_name()

    def get_root_node(self):
        self._set_parser()
        return self._parser.get_root_node()

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

    def _set_uuid(self):
        if self.xml and not self.uuid:
            uuid = get_uuid_from_xml(self.xml)
            if uuid is not None:
                self.uuid = uuid
        set_uuid(self)

    def save(self, *args, **kwargs):
        self._set_xform(get_id_string_from_xml_str(self.xml))
        doc = self.get_dict()
        if self.xform and not self.xform.downloadable:
            raise FormInactiveError()
        self._set_start_time(doc)
        self._set_date(doc)
        self._set_survey_type(doc)
        self._set_uuid()
        super(Instance, self).save(*args, **kwargs)

    def _set_parser(self):
        if not hasattr(self, "_parser"):
            self._parser = XFormInstanceParser(
                self.xml, self.xform.data_dictionary())

    def get_dict(self, force_new=False, flat=True):
        """Return a python object representation of this instance's XML."""
        self._set_parser()
        if flat:
            return self._parser.get_flat_dict_with_attributes()
        else:
            return self._parser.to_dict()

    def set_deleted(self, deleted_at=timezone.now()):
        self.deleted_at = deleted_at
        self.is_deleted = True
        self.save()
        self.parsed_instance.save()

    @classmethod
    def set_deleted_at(cls, instance_id, deleted_at=timezone.now()):
        try:
            instance = cls.objects.get(id=instance_id)
        except cls.DoesNotExist:
            pass
        else:
            instance.set_deleted(deleted_at)


def update_xform_submission_count(sender, instance, created, **kwargs):
    if created:
        xform = XForm.objects.select_related().select_for_update()\
            .get(pk=instance.xform.pk)
        if xform.num_of_submissions == -1:
            xform.num_of_submissions = 0
        xform.num_of_submissions += 1
        xform.last_submission_time = instance.date_created
        xform.save()
        profile_qs = User.profile.get_query_set()
        try:
            profile = profile_qs.select_for_update()\
                .get(pk=xform.user.profile.pk)
        except profile_qs.model.DoesNotExist:
            pass
        else:
            profile.num_of_submissions += 1
            profile.save()

post_save.connect(update_xform_submission_count, sender=Instance,
                  dispatch_uid='update_xform_submission_count')


def update_xform_submission_count_delete(sender, instance, **kwargs):
    try:
        xform = XForm.objects.select_for_update().get(pk=instance.xform.pk)
    except XForm.DoesNotExist:
        pass
    else:
        xform.num_of_submissions -= 1
        if xform.num_of_submissions < 0:
            xform.num_of_submissions = 0
        xform.save()
        profile_qs = User.profile.get_query_set()
        try:
            profile = profile_qs.select_for_update()\
                .get(pk=xform.user.profile.pk)
        except profile_qs.model.DoesNotExist:
            pass
        else:
            profile.num_of_submissions -= 1
            if profile.num_of_submissions < 0:
                profile.num_of_submissions = 0
            profile.save()

post_delete.connect(update_xform_submission_count_delete, sender=Instance,
                    dispatch_uid='update_xform_submission_count_delete')


class InstanceHistory(models.Model):
    class Meta:
        app_label = 'odk_logger'

    xform_instance = models.ForeignKey(
        Instance, related_name='submission_history')
    xml = models.TextField()
    # old instance id
    uuid = models.CharField(max_length=249, default=u'')

    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
