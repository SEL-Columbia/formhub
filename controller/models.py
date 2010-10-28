from django.db import models
from django.db.models.signals import post_save

from xml.sax.handler import ContentHandler
from xml.sax import parseString

from odk_dropbox.models import Submission
from eav.models import Attribute, Value

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
        a = Attribute.objects.get(slug=name)
        o = Value(entity=self._stack.top(), attribute=a)
        self._stack.append(o)
        self._objects.append(o)

        # make sure there are no attributes
        assert attrs.getLength()==0, "This parser is not equipped to handle attributes."

    def characters(self, content):
        # ignore whitespace
        s = content.strip()
        if s:
            # set the value of the eav.Value on the top of the stack
            self._stack.top().value = content

    def endElement(self, name):
        top = self._stack.pop()
        assert name==top.attribute.slug, "endElement doesn't match last startElement"


def add_to_eav(submission):
    handler = EAVHandler(submission)
    parseString(submission.xml, handler)
    # save all the objects created by parsing the submission's xml
    for o in handler.get_objects:
        o.save()

def _add_to_eav(sender, **kwargs):
    # if this is a new submission add it to the eav
    if kwargs["created"]:
        add_to_eav(kwargs["instance"])

post_save.connect(_add_to_eav, sender=Submission)
