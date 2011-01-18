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

class Form(models.Model):
    xml_file = models.FileField(
        upload_to=FORM_PATH, verbose_name="XML File"
        )
    active = models.BooleanField()
    description = models.TextField(blank=True, null=True, default="")
    id_string = models.CharField(
        unique=True, editable=False, verbose_name="ID String", max_length=64
        )
    title = models.CharField(editable=False, max_length=64)

    class Meta:
        verbose_name = "XForm"
        verbose_name_plural = "XForms"
        ordering = ("id_string",)

    def save(self, *args, **kwargs):
        form_parser = utils.FormParser(self.xml_file)
        self.id_string = form_parser.get_id_string()
        self.title = form_parser.get_title()
        if Form.objects.filter(title=self.title, active=True).count()>0:
            raise Exception("We can only have a single active form with a particular title")
        super(Form, self).save(*args, **kwargs)

    def __unicode__(self):
        return getattr(self, "id_string", "")

    def path(self):
        return settings.MEDIA_ROOT + self.xml_file.name

    def url(self):
        return self.xml_file.url

    def slug(self):
        return self.id_string
        return utils.sluggify(self.id_string)

    def submission_count(self):
        return self.instances.all().count()
    submission_count.short_description = "Submission Count"

    def date_of_last_submission(self):
        qs = Submission.objects.filter(instance__form=self).order_by("-posted")
        if qs.count()>0:
            return qs[0].posted


# http://docs.djangoproject.com/en/dev/ref/models/fields/#django.db.models.FileField.upload_to
def _upload_xml_file(instance, filename):
    def _drop_xml_extension(filename):
        m = re.search(r"^(.*)\.xml$", filename)
        if m:
            return m.group(1)
        else:
            raise Exception("Filename must end with '.xml'", filename)
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

    class Meta:
        ordering = ("posted",)

# COUCHDBKIT STUFF

import couchdbkit

class ODKInstance(couchdbkit.Document):
    pass

server = couchdbkit.Server()
odk_db = server.get_or_create_db("odk")
ODKInstance.set_db(odk_db)

def make_submission(xml_file, media_files):
    """
    I used to check if this file had been submitted already, I've
    taken this out because it was too slow. Now we're going to create
    a way for an admin to mark duplicate submissions. This should
    simplify things a bit.
    """
    doc = ODKInstance()
    doc.save()

    # attach all the files
    for f in [xml_file] + media_files: doc.put_attachment(f)

    # putting the xml_file up as an attachment reads the file
    xml_file.seek(0)

    # add the parsed xml
    data = utils.parse_odk_xml(xml_file)
    doc.parsed_xml = data
    doc.save()
