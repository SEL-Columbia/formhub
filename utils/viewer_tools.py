import os, sys
import traceback
from xml.dom import minidom

from django.conf import settings
from django.core.files.storage import get_storage_class
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.mail import mail_admins

import common_tags as tag


SLASH = u"/"


class MyError(Exception):
    pass


def image_urls_for_form(xform):
    return sum([
        image_urls(s) for s in xform.surveys.all()
    ], [])


def get_path(path, suffix):
    fileName, fileExtension = os.path.splitext(path)
    return fileName + suffix +  fileExtension


def image_urls(instance):
    default_storage = get_storage_class()()
    return [ default_storage.url(get_path(a.media_file.name,
            settings.THUMB_CONF['medium']['suffix'])) if
            default_storage.exists(get_path(a.media_file.name,
            settings.THUMB_CONF['medium']['suffix'])) else
            a.media_file.url for a in instance.attachments.all()]


def parse_xform_instance(xml_str):
    """
    'xml_str' is a str object holding the XML of an XForm
    instance. Return a python object representation of this XML file.
    """
    xml_obj = minidom.parseString(xml_str)
    root_node = xml_obj.documentElement
    # go through the xml object creating a corresponding python object
    # NOTE: THIS WILL DESTROY ANY DATA COLLECTED WITH REPEATABLE NODES
    # THIS IS OKAY FOR OUR USE CASE, BUT OTHER USERS SHOULD BEWARE.
    survey_data = dict(_path_value_pairs(root_node))
    assert len(list(_all_attributes(root_node)))==1, \
        u"There should be exactly one attribute in this document."
    survey_data.update({
            tag.XFORM_ID_STRING : root_node.getAttribute(u"id"),
            tag.INSTANCE_DOC_NAME : root_node.nodeName,
            })
    return survey_data


def _path(node):
    n = node
    levels = []
    while n.nodeType!=n.DOCUMENT_NODE:
        levels = [n.nodeName] + levels
        n = n.parentNode
    return SLASH.join(levels[1:])


def _path_value_pairs(node):
    """
    Using a depth first traversal of the xml nodes build up a python
    object in parent that holds the tree structure of the data.
    """
    if len(node.childNodes)==0:
        # there's no data for this leaf node
        yield _path(node), None
    elif len(node.childNodes)==1 and \
            node.childNodes[0].nodeType==node.TEXT_NODE:
        # there is data for this leaf node
        yield _path(node), node.childNodes[0].nodeValue
    else:
        # this is an internal node
        for child in node.childNodes:
            for pair in _path_value_pairs(child):
                yield pair


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


class XFormParser(object):

    def __init__(self, xml):
        assert type(xml)==str or type(xml)==unicode, u"xml must be a string"
        self.doc = minidom.parseString(xml)
        self.root_node = self.doc.documentElement

    def get_variable_list(self):
        """
        Return a list of pairs [(path to variable1, attributes of variable1),
        ...].
        """
        bindings = self.doc.getElementsByTagName(u"bind")
        attributes = [dict(_all_attributes(b)) for b in bindings]
        # note: nodesets look like /water/source/blah we're returning
        # source/blah
        return [
            (SLASH.join(d.pop(u"nodeset").split(SLASH)[2:]), d)
            for d in attributes
        ]

    def get_variable_dictionary(self):
        d = {}
        for path, attributes in self.get_variable_list():
            assert path not in d, u"Paths should be unique."
            d[path] = attributes
        return d

    def follow(self, path):
        """
        Path is an array of node names. Starting at the document
        element we follow the path, returning the final node in the
        path.
        """
        element = self.doc.documentElement
        count = {}
        for name in path.split(SLASH):
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
        instance = self.follow(u"h:head/model/instance")
        children = [child for child in instance.childNodes \
                        if isinstance(child, minidom.Element)]
        assert len(children)==1
        return children[0].getAttribute(u"id")

    def get_title(self):
        title = self.follow(u"h:head/h:title")
        assert len(title.childNodes)==1, u"There should be a single title"
        return title.childNodes[0].nodeValue

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


def report_exception(subject, info, exc_info=None):
    if exc_info:
        cls, err = exc_info[:2]
        info += u"Exception in request: %s: %s" % (cls.__name__, err)
        info += u"".join(traceback.format_exception(*exc_info))

    if settings.DEBUG:
        print subject
        print info
    else:
        mail_admins(subject=subject, message=info)


def django_file(path, field_name, content_type):
    # adapted from here:
    # http://groups.google.com/group/django-users/browse_thread/thread/834f988876ff3c45/
    f = open(path)
    return InMemoryUploadedFile(
        file=f,
        field_name=field_name,
        name=f.name,
        content_type=content_type,
        size=os.path.getsize(path),
        charset=None
        )
