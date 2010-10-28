from django.db import models
from django.db.models.signals import post_save

from xml.sax.handler import ContentHandler
from xml.sax import parseString

from odk_dropbox.models import Submission
from eav.models import Attribute, Value
from eav.fields import EavSlugField

class EAVHandler(ContentHandler):

    def __init__ (self, submission):
        # The stack should start with the ODK Submission
        self._stack = [submission]
        self._objects = []

    def get_objects(self):
        return self._objects

    def startElement(self, name, attrs):
        # Create a new eav.Value
        # the entity is the top of stack
        # the attribute is shares the name of this tag
        print "startElement:", name
        slug = EavSlugField.create_slug_from_name(name)
        try:
            a = Attribute.objects.get(slug=slug)
        except Attribute.DoesNotExist as e:
            d = {"slug" : slug,
                 "datatype" : Attribute.TYPE_TEXT,
                 "name" : name,}
            a = Attribute.objects.create(**d)
        o = Value(entity=self._stack[-1], attribute=a)

        # Unfortunately I have to save the object here so that
        # subsequent objects can reference it.
        o.save()
        self._stack.append(o)
        self._objects.append(o)

        # make sure there are no attributes
        if attrs.getLength() > 0:
            print "We're ignoring some attributes here."

    def characters(self, content):
        # ignore whitespace
        s = content.strip()
        if s:
            # set the value of the eav.Value on the top of the stack
            # and update it in the database
            print "content:", content
            self._stack[-1].value = content
            self._stack[-1].save()

    def endElement(self, name):
        slug = EavSlugField.create_slug_from_name(name)
        print "endElement:", name
        top = self._stack.pop()
        assert slug==top.attribute.slug, "endElement doesn't match last startElement"


def add_to_eav(submission):
    handler = EAVHandler(submission)
    byte_string = submission.xml.encode( "utf-8" )
    parseString(byte_string, handler)

def _add_to_eav(sender, **kwargs):
    # if this is a new submission add it to the eav
    if kwargs["created"]:
        add_to_eav(kwargs["instance"])

post_save.connect(_add_to_eav, sender=Submission)
