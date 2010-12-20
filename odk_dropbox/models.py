#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import os, re, sys
from xml.dom.minidom import parseString, Element
from django.db import models
from django.db.models.signals import pre_save
from django.conf import settings
from . import utils

FORM_PATH = "odk/forms"
INSTANCE_PATH = "odk/instances"

def _drop_xml_extension(filename):
    """
    Return the filename having dropped the 'xml' extension. If the
    filename didn't end with '.xml' raise an exception.
    """    
    m = re.search(r"(.*)\.xml$", filename)
    if m:
        return m.group(1)
    else:
        raise Exception("Filename must end with '.xml'", filename)

class Form(models.Model):
    xml_file = models.FileField(
        upload_to=FORM_PATH, verbose_name="XML File"
        )
    id_string = models.CharField(
        unique=True, blank=True, max_length=32, verbose_name="ID String"
        )
    active = models.BooleanField()

    class Meta:
        verbose_name = "XForm for ODK"
        verbose_name_plural = "XForms for ODK"

    def __unicode__(self):
        return getattr(self, "id_string", "")

    def path(self):
        return settings.MEDIA_ROOT + self.xml_file.name

    def name(self):
        folder, filename = os.path.split(self.path())
        return _drop_xml_extension(filename)

    def url(self):
        return self.xml_file.url

    def _set_id_from_xml(self):
        """
        Find the single child of h:head/model/instance and return the
        attribute 'id'.
        """
        xml = utils.text(self.xml_file)
        dom = parseString(xml)
        element = dom.documentElement
        path = ["h:head", "model", "instance"]
        count = {}
        for name in path:
            count[name] = 0
            for child in element.childNodes:
                if isinstance(child, Element) and child.tagName==name:
                    count[name] += 1
                    element = child
            assert count[name]==1
        count["id"] = 0
        for child in element.childNodes:
            if isinstance(child, Element):
                count["id"] += 1
                element = child
        assert count["id"]==1
        self.id_string = element.getAttribute("id")

# before a form is saved to the database set the form's id string by
# looking through it's xml.
def _set_form_id(sender, **kwargs):
    kwargs["instance"]._set_id_from_xml()

pre_save.connect(_set_form_id, sender=Form)

    
# http://docs.djangoproject.com/en/dev/ref/models/fields/#django.db.models.FileField.upload_to
def _upload_xml_file(instance, filename):
    folder_name = _drop_xml_extension(filename)
    return os.path.join(INSTANCE_PATH, folder_name, filename)

def hash_contents(f):
    """
    Return a hash code of the contents of the file f.
    """
    s = utils.text(f)
    return s.__hash__()

class Instance(models.Model):
    xml_file = models.FileField(upload_to=_upload_xml_file)
    form = models.ForeignKey(Form, blank=True, null=True, related_name="instances")
    hash = models.IntegerField(blank=True, null=True)

    def __unicode__(self):
        if self.form:
            return self.form.__unicode__()
        else:
            return "no link"

    def _set_hash(self):
        self.hash = hash_contents(self.xml_file)

    def _link(self):
        """Link this instance to the form with same id field."""
        try:
            handler = utils.parse_instance(self)
            id_string = handler.get_form_id()
            self.form = Form.objects.get(id_string=id_string)
        except Form.DoesNotExist:
            utils.report_exception(
                "missing original form",
                "This instance cannot be linked to the original form because we no longer have %s." % id_string
                )
        except:
            utils.report_exception(
                "problem linking instance",
                "This is probably a problem parsing the instance.",
                sys.exc_info()
                )

def _setup_instance(sender, **kwargs):
    kwargs["instance"]._set_hash()
    kwargs["instance"]._link()

pre_save.connect(_setup_instance, sender=Instance)

    
def _upload_image(instance, filename):
    """
    Save this image in the same folder as its instance.
    """
    folder, xml_filename = os.path.split(instance.instance.xml_file.name)
    return os.path.join(folder, filename)

class InstanceImage(models.Model):
    instance = models.ForeignKey(Instance, related_name="images")
    image = models.FileField(upload_to=_upload_image)

class Submission(models.Model):
    posted = models.DateTimeField(auto_now_add=True)
    instance = models.ForeignKey(Instance, related_name="submissions")

def make_submission(xml_file, images):
    """
    If this XML file is already in the database log that this file has
    been submitted a second time and return the submission
    object. Otherwise save this file to the database and return the
    submission object.
    """
    matches = Instance.objects.filter(hash=hash_contents(xml_file))
    text = utils.text(xml_file)
    for match in matches:
        if utils.text(match.xml_file)==text:
            return Submission.objects.create(instance=match)
    instance = Instance.objects.create(xml_file=xml_file)
    for image in images:
        InstanceImage.objects.create(instance=instance, image=image)
    return Submission.objects.create(instance=instance)
