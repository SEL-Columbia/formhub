#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.db import models
from django.db.models.signals import pre_save
from xml.dom.minidom import parseString, Element
import os, re, sys

from . import utils

FORM_PATH = "odk/forms"
INSTANCE_PATH = "odk/instances"

def _drop_xml_extension(str):
    m = re.search(r"(.*)\.xml$", str)
    if m:
        return m.group(1)
    else:
        raise Exception("This string doesn't end with .xml. " + str)

class Form(models.Model):
    xml_file = models.FileField(upload_to=FORM_PATH)
    id_string = models.CharField(unique=True, blank=True, max_length=32)
    active = models.BooleanField()

    def __unicode__(self):
        return getattr(self, "id_string", "")

    def name(self):
        head, tail = os.path.split(self.xml_file.name)
        return _drop_xml_extension(tail)

    def url(self):
        return self.xml_file.url

    def _set_id_from_xml(self):
        """Find the single child of h:head/model/instance and return
        the attribute 'id'."""
        self.xml_file.open()
        xml = self.xml_file.read()
        self.xml_file.close()
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
def _upload_submission(instance, filename):
    folder_name = _drop_xml_extension(filename)
    return os.path.join(INSTANCE_PATH, folder_name, filename)

class Submission(models.Model):
    xml_file = models.FileField(upload_to=_upload_submission)
    form = models.ForeignKey(Form, blank=True, null=True, related_name="submissions")
    posted = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        if self.form:
            return self.form.__unicode__()
        else:
            return "no link"

    def _link(self):
        """Link this submission to the form with same id field."""
        self.xml_file.open()
        xml = self.xml_file.read()
        self.xml_file.close()
        try:
            handler = utils.parse(xml)
            id_string = handler.get_form_id()
            self.form = Form.objects.get(id_string=id_string)
        except Form.DoesNotExist:
            utils.report_exception(
                "missing original form",
                "This submission cannot be linked to the original form because we no longer have %s." % id_string
                )
        except:
            utils.report_exception(
                "problem linking submission",
                "This is probably a problem parsing the submission.",
                sys.exc_info()
                )


def _link_submission(sender, **kwargs):
    kwargs["instance"]._link()

pre_save.connect(_link_submission, sender=Submission)

    
def _upload_image(instance, filename):
    """Save this image in the same folder as its submission."""
    head, tail = os.path.split(instance.submission.xml_file.name)
    return os.path.join(head, filename)

class SubmissionImage(models.Model):
    submission = models.ForeignKey(Submission, related_name="images")
    image = models.FileField(upload_to=_upload_image)
