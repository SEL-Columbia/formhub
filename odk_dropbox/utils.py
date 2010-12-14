#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from xml.sax.handler import ContentHandler
from xml.sax import parseString

class ODKHandler(ContentHandler):

    def __init__ (self):
        self._dict = {}
        self._stack = []
        self._form_id = ""
        self._repeated_tags = []

    def get_dict(self):
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
            assert len(self._stack)==1, "Attributes should be associated with the root node only."
            for key in attrs.keys():
                assert key=="id", "The only attribute we should see is an 'id'."
                self._form_id = attrs.get(key)

    def characters(self, content):
        # ignore whitespace
        s = content.strip()
        if s:
            tag = self._stack[-1]
            if tag not in self._dict:
                self._dict[tag] = s
            else:
                self._repeated_tags.append( "/".join(self._stack) )

    def endElement(self, name):
        top = self._stack.pop()
        assert top==name, "start element %(top)s doesn't match end element %(name)s" % {"top" : top, "name" : name}


def parse(xml):
    handler = ODKHandler()
    repeats = handler.get_repeated_tags()
    if repeats:
        report_exception(
            "XML tags should be unique",
            "\n".join(handler.get_repeated_tags())
            )
    byte_string = xml.encode("utf-8")
    parseString(byte_string, handler)
    return handler

def text(file):
    file.open()
    text = file.read()
    file.close()
    return text

def parse_submission(submission):
    return parse(text(submission.xml_file))


def table(dicts):
    """Turn a list of dicts into a table."""
    # Note: we're doing everything in memory because it's easier.
    headers = []
    for dict in dicts:
        for key in dict.keys():
            if key not in headers:
                headers.append(key)
    headers.sort()
    table = [headers]
    for dict in dicts:
        row = []
        for header in headers:
            if header in dict:
                row.append(dict[header])
            else:
                row.append("")
        table.append(row)
    return table

def csv(table):
    csv = ""
    for row in table:
        csv += ",".join(['"' + cell + '"' for cell in row])
        csv += "\n"
    return csv

from django.core.mail import mail_admins
import traceback
def report_exception(subject, info, exc_info=None):
    if exc_info:
        try:
            cls, err = exc_info[:2]
            info += "Exception in request: %s: %s" % (cls.__name__, err)
            info += "".join(traceback.format_exception(*exc_info))
        except:
            report_exception("problem reporting exception",
                             "i'll test this late at night.")

    # fail silently is good for development settings
    mail_admins(subject=subject, message=info, fail_silently=True)
