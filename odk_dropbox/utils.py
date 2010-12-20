#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from xml.sax.handler import ContentHandler
from xml.sax import parseString
import xml

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
        if tag not in self._dict:
            # if we haven't seen this tag before just add this key
            # value pair to the dictionary
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

def get_variable_name(binding):
    return binding.getAttribute("nodeset").split("/")[-1]

class XMLParser(object):
    def __init__(self, path):
        self.doc = xml.dom.minidom.parse(path)

class FormParser(XMLParser):
    def get_bindings(self):
        return self.doc.getElementsByTagName("bind")

    def get_variable_list(self):
        return [get_variable_name(b) for b in self.get_bindings()]


def table(form):
    """Turn a list of dicts into a table."""
    form_parser = FormParser(form.path())
    headers = form_parser.get_variable_list()

    table = [headers]
    for i in form.instances.all():
        d = parse_instance(i).get_dict()
        table.append( [d.get(header, u".") for header in headers] )
    return table

def csv(table):
    csv = ""
    for row in table:
        csv += ",".join(['"' + cell + '"' for cell in row])
        csv += "\n"
    return csv

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
