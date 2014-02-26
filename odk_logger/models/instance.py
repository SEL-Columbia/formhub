from xml.dom import minidom, Node
from django.db import models
from django.db.models.loading import get_model
from django.contrib.auth.models import User
from django.utils import timezone
from .xform import XForm
from .survey_type import SurveyType
from odk_logger.xform_instance_parser import XFormInstanceParser, \
    clean_and_parse_xml, get_uuid_from_xml
from utils.model_tools import set_uuid
from utils.stathat_api import stathat_count
from celery import task
from django.utils.translation import ugettext as _
from taggit.managers import TaggableManager

class FormInactiveError(Exception):
    def __unicode__(self):
        return _("Form is inactive")

    def __str__(self):
        return unicode(self).encode('utf-8')

@task
def create_flattened_instance(instance):
    doc = minidom.parseString(instance.xml)
    root_doc = doc.firstChild
    #the dictionary is just used to find the right repeating group, it's probably possible to remove this
    dd = instance.get_dict()
    repeats = [e.get_abbreviated_xpath() for e in instance.xform.data_dictionary().get_survey_elements_of_type(u"repeat")]
    #for each repeating group...
    for repeat in repeats:
        if repeat in dd:
            #we get the node that contains the targeted repeating group
            repeat_nodes = doc.getElementsByTagName(repeat)
            #we clonde each node insisde the repeating group
            #we need to use cloneNode, otherwise we just get a reference to the node (and we'll lose it on deletion)
            xml_repeats_clone = [node.cloneNode(True) for node in repeat_nodes if not node.hasAttribute('template') ]
            #we remove the repeating group of our document, to get the base
            for r in repeat_nodes:
                old = doc.firstChild.removeChild(r)
                old.unlink()
            #we append ecah repeating group to his own document
            #and we create an instance of Instance and ParsedInstance with each of these documents
            for el in xml_repeats_clone:
                new_doc = root_doc.cloneNode(True)
                new_doc.appendChild(el)
                FlattenedInstance = get_model('odk_viewer', 'FlattenedInstance')
                print new_doc.toprettyxml()
                FlattenedInstance.objects.create(
                    xml=new_doc.toxml(),
                    instance=instance
                )


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

    def get_flattened_instance(self):
        if not self.flattened_instance:
            return instance.parsed_instance
        else:
            return self.flattened_instance

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
        create_flattened_instance(self)

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


def stathat_form_submission(sender, instance, created, **kwargs):
    if created:
        stathat_count('formhub-submissions')


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
