#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# import ipdb; ipdb.set_trace()

from xml.dom import minidom
import os, sys

def parse_odk_xml(f):
    """
    'f' may be a file object or a path to a file. Return a python
    object representation of this XML file.
    """
    xml_obj = minidom.parse(f)
    root_node = xml_obj.documentElement
    # go through the xml object creating a corresponding python object
    survey_data = {}
    _build(root_node, survey_data)
    keys = survey_data.keys()
    assert len(keys)==1, "There should be a single root node."
    assert len(list(_all_attributes(root_node)))==1, \
        u"There should be exactly one attribute in this document."
    # return the document id, and the newly constructing python object
    return {"form_id" : root_node.getAttribute(u"id"),
            "survey_type" : keys[0],
            "survey_data" : survey_data[keys[0]],}

def _build(node, parent):
    """
    Using a depth first traversal of the xml nodes build up a python
    object in parent that holds the tree structure of the data.
    """
    if node.nodeName in parent:
        raise Exception("We aren't equipped to do repeating nodes.")

    if len(node.childNodes)==0:
        # there's no data for this leaf node
        parent[node.nodeName] = None
    elif len(node.childNodes)==1 and \
            node.childNodes[0].nodeType==node.TEXT_NODE:
        # there is data for this leaf node
        parent[node.nodeName] = node.childNodes[0].nodeValue
    else:
        # this is an internal node
        parent[node.nodeName] = {}
        for child in node.childNodes:
            _build(child, parent[node.nodeName])

def _all_attributes(node):
    """
    Go through an XML document returning all the attributes we see.
    """
    if hasattr(node, "hasAttributes") and node.hasAttributes():
        for key in node.attributes.keys():
            yield key, node.getAttribute(key)
    for child in node.childNodes:
        for pair in _all_attributes(child):
            yield pair


# import json ; print json.dumps(parse_odk_xml(sys.argv[1]), indent=4)


class VariableDictionary(object):
    def __init__(self, d):
        """
        The keys of this dictionary are paths to variables and the
        values are a bunch of attributes
        """
        self._d = d

    def __getitem__(self, key):
        if key in self._d: return self._d[key]
        # otherwise
        result = {}
        for k in self._d.keys():
            if k.startswith(key + "/"):
                result[k[len(key)+1:]] = self._d[k]
        return VariableDictionary(result)

# test = {"one/two" : 1, "one/three" : 3, "two" : 2}
# vardict = VariableDictionary(test)
# print vardict["one"]._d, vardict["two"]

class XFormParser(object):
    def __init__(self, xml):
        """'f' is either a path to a file, or a file object."""
        self.doc = minidom.parseString(xml)
        self.root_node = self.doc.documentElement

    def get_variable_list(self):
        """
        Return a list of pairs [(path to variable1, attributes of variable1), ...].
        """
        bindings = self.doc.getElementsByTagName("bind")
        attributes = [dict(_all_attributes(b)) for b in bindings]
        # note: nodesets look like /water/source/blah we're returning ['source', 'blah']
        return [(d.pop("nodeset").split("/")[2:], d) for d in attributes]

    def get_variable_dictionary(self):
        d = {}
        for path, attributes in self.get_variable_list():
            path = "/".join(path)
            assert path not in d, "Paths should be unique."
            d[path] = attributes
        return VariableDictionary(d)

    def follow(self, path):
        """
        Path is an array of node names. Starting at the document
        element we follow the path, returning the final node in the
        path.
        """
        element = self.doc.documentElement
        count = {}
        for name in path.split("/"):
            count[name] = 0
            for child in element.childNodes:
                if isinstance(child, minidom.Element) and child.tagName==name:
                    count[name] += 1
                    element = child
            assert count[name]==1
        return element

    def get_id_string(self):
        """
        Find the single child of h:head/model/instance and return the
        attribute 'id'.
        """
        instance = self.follow("h:head/model/instance")
        children = [child for child in instance.childNodes \
                        if isinstance(child, minidom.Element)]
        assert len(children)==1
        return children[0].getAttribute("id")

    def get_title(self):
        title = self.follow("h:head/h:title")
        assert len(title.childNodes)==1, "There should be a single title"
        return title.childNodes[0].nodeValue


def json_value(x, path):
    """
    Assuming that x is a Python representation of a JSON object,
    follow the key path to return a value. Raise an exception if the
    value isn't found.
    https://github.com/dimagi/couchforms/blob/master/couchforms/safe_index.py
    """
    if len(path)>1: return json_value(x[path[0]], path[1:])
    return x[path[0]]


# xform = XFormDocument(sys.argv[1])
# import json ; print json.dumps(xform.get_variables(), indent=4)


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
