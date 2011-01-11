#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from xml.sax.handler import ContentHandler
from xml.sax import parseString
import xml
from xml.dom.minidom import Element
import re, os

class ODKHandler(ContentHandler):

    def __init__ (self):
        self._dict = {}
        self._stack = []
        self._form_id = ""

    def get_dict(self):
        # Note: we're only using the xml tag in our dictionary, not
        # the whole xpath.
        return self._dict

    def get_form_id(self):
        return self._form_id

    def get_repeated_tags(self):
        return self._repeated_tags

    def startElement(self, name, attrs):
        self._stack.append(name)

        if name not in self._dict: self._dict[name] = u""

        # there should only be a single attribute in this document
        # an id on the root node
        if attrs:
            assert len(self._stack)==1, \
                "Attributes should only be on the root node."
            keys = attrs.keys()
            assert keys==["id"], \
                "The only attribute we should see is an 'id'."
            self._form_id = attrs.get("id")

    def characters(self, content):
        # ignore whitespace
        s = content.strip()
        if not s: return

        # get the last tag we saw
        tag = self._stack[-1]
        if not self._dict[tag]:
            # if we haven't seen a value for this tag yet
            self._dict[tag] = s
        else:
            # if we have seen this tag before we need to append this
            # value to a list of all the values we've seen before
            self._dict[tag] += u" " + s

    def endElement(self, name):
        top = self._stack.pop()
        assert top==name, \
            "start %(top)s doesn't match end %(name)s" % \
            {"top" : top, "name" : name} 


def parse(xml):
    handler = ODKHandler()
    byte_string = xml.encode("utf-8")
    parseString(byte_string, handler)

    d = handler.get_dict()
    repeats = [(k,v) for k, v in d.items() if type(v)==list]
    if repeats: report_exception("Repeated XML tags", str(repeats))

    return handler

def text(file):
    """
    Return the string contents of the passed file.
    """
    file.open()
    text = file.read()
    file.close()
    return text

def parse_instance(instance):
    """
    Return the ODKHandler from parsing the xml_file of this instance.
    """
    return parse(text(instance.xml_file))

def sluggify(text, delimiter=u"_"):
    return re.sub(r"\W+", delimiter, text.lower())

## PARSING OF XFORMS
# at each text node we grab the nodeValue
# and parentNode.nodeName
def get_text_nodes(node):
    if node.nodeType == node.TEXT_NODE:
        return [node]
    else:
        result = []
        for n in node.childNodes:
            result += get_text_nodes(n)
        return result

def follow(element, path):
    """
    Path is an array of node names. Starting at the document
    element we follow the path, returning the final node in the
    path.
    """
    count = {}
    for name in path.split("/"):
        count[name] = 0
        for child in element.childNodes:
            if isinstance(child, Element) and child.tagName==name:
                count[name] += 1
                element = child
        assert count[name]==1
    return element

class XMLParser(object):
    def __init__(self, x):
        """
        x is either a path to a file, or a file object.
        """
        if hasattr(x, "open") and hasattr(x, "read") and hasattr(x, "close"):
            self.doc = xml.dom.minidom.parseString(text(x))
        else:
            self.doc = xml.dom.minidom.parse(x)

    def follow(self, path):
        return follow(self.doc.documentElement, path)

def get_text(node_list):
    text_nodes = [node for node in node_list if node.nodeType==node.TEXT_NODE]
    return " ".join([node.data for node in text_nodes])

def get_nodeset(binding):
    return binding.getAttribute("nodeset")

def get_name(binding):
    return get_nodeset(binding).split("/")[-1]

class FormParser(XMLParser):
    def get_bindings(self):
        return self.doc.getElementsByTagName("bind")

    def get_variable_list(self):
        return [get_name(b) for b in self.get_bindings()]

    def get_id_string(self):
        """
        Find the single child of h:head/model/instance and return the
        attribute 'id'.
        """
        instance = self.follow("h:head/model/instance")
        children = [child for child in instance.childNodes \
                        if isinstance(child, Element)]
        assert len(children)==1
        return children[0].getAttribute("id")

    def get_title(self):
        title = self.follow("h:head/h:title")
        return get_text(title.childNodes)

    supported_controls = ["input", "select1", "select", "upload"]

    def get_control_dict(self):
        def get_pairs(e):
            result = []
            if hasattr(e, "tagName") and e.tagName in self.supported_controls:
                result.append( (e.getAttribute("ref"),
                                get_text(follow(e, "label").childNodes)) )
            if e.hasChildNodes:
                for child in e.childNodes:
                    result.extend(get_pairs(child))
            return result
        return dict(get_pairs(self.follow("h:body")))

    def get_dictionary(self):
        d = self.get_control_dict()
        return [(get_name(b), d.get(get_nodeset(b),"")) for b in self.get_bindings()]

from django.conf import settings
from django.core.mail import mail_admins
import traceback
def report_exception(subject, info, exc_info=None):
    if exc_info:
        cls, err = exc_info[:2]
        info += "Exception in request: %s: %s" % (cls.__name__, err)
        info += "".join(traceback.format_exception(*exc_info))

    if settings.DEBUG:
        print subject
        print info
    else:
        mail_admins(subject=subject, message=info)
        
from django.core.files.uploadedfile import InMemoryUploadedFile
def django_file(path, field_name, content_type):
    # adapted from here: http://groups.google.com/group/django-users/browse_thread/thread/834f988876ff3c45/
    f = open(path)
    return InMemoryUploadedFile(
        file=f,
        field_name=field_name,
        name=f.name,
        content_type=content_type,
        size=os.path.getsize(path),
        charset=None
        )
