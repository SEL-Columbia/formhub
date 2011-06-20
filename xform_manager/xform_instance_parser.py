# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from xml.dom import minidom
import re

XFORM_ID_STRING = u"_xform_id_string"

def _xml_node_to_dict(node):
    assert isinstance(node, minidom.Node)
    if len(node.childNodes)==0:
        # there's no data for this leaf node
        value = None
    elif len(node.childNodes)==1 and \
            node.childNodes[0].nodeType==node.TEXT_NODE:
        # there is data for this leaf node
        value = node.childNodes[0].nodeValue
    else:
        # this is an internal node
        value = {}
        for child in node.childNodes:
            d = _xml_node_to_dict(child)
            child_name = child.nodeName
            assert d.keys()==[child_name]
            if child_name not in value:
                # copy the value into the dict
                value[child_name] = d[child_name]
            elif type(value[child_name])==list:
                # add to the existing list
                value[child_name].append(d[child_name])
            else:
                # create a new list
                value[child_name] = [value[child_name], d[child_name]]
    return {node.nodeName: value}

def _flatten_dict(d, prefix):
    """
    Return a list of XPath, value pairs.
    """
    assert type(d)==dict
    assert type(prefix)==list

    for key, value in d.items():
        new_prefix = prefix + [key]
        if type(value)==dict:
            for pair in _flatten_dict(value, new_prefix):
                yield pair
        elif type(value)==list:
            for i, item in enumerate(value):
                item_prefix = list(new_prefix) # make a copy
                # note on indexing xpaths: IE5 and later has
                # implemented that [0] should be the first node, but
                # according to the W3C standard it should have been
                # [1]. I'm adding 1 to i to start at 1.
                item_prefix[-1] += u"[%s]" % unicode(i+1)
                if type(item)==dict:
                    for pair in _flatten_dict(item, item_prefix):
                        yield pair
                else:
                    yield (item_prefix, item)
        else:
            yield (new_prefix, value)

def _get_all_attributes(node):
    """
    Go through an XML document returning all the attributes we see.
    """
    if hasattr(node, "hasAttributes") and node.hasAttributes():
        for key in node.attributes.keys():
            yield key, node.getAttribute(key)
    for child in node.childNodes:
        for pair in _get_all_attributes(child):
            yield pair


class XFormInstanceParser(object):

    def __init__(self, xml_str):
        self.parse(xml_str)

    def parse(self, xml_str):
        clean_xml_str = xml_str.strip()
        clean_xml_str = re.sub(ur">\s+<", u"><", clean_xml_str)
        self._xml_obj = minidom.parseString(clean_xml_str)
        self._root_node = self._xml_obj.documentElement
        self._dict = _xml_node_to_dict(self._root_node)
        self._flat_dict = {}
        for path, value in _flatten_dict(self._dict, []):
            self._flat_dict[u"/".join(path[1:])] = value
        self._set_attributes()

    def get_root_node_name(self):
        return self._root_node.nodeName

    def get(self, abbreviated_xpath):
        return self.to_flat_dict()[abbreviated_xpath]

    def to_dict(self):
        return self._dict

    def to_flat_dict(self):
        return self._flat_dict

    def get_attributes(self):
        return self._attributes

    def _set_attributes(self):
        self._attributes = {}
        all_attributes = list(_get_all_attributes(self._root_node))
        for key, value in all_attributes:
            assert key not in self._attributes
            self._attributes[key] = value

    def get_xform_id_string(self):
        return self._attributes[u"id"]

    def get_flat_dict_with_attributes(self):
        result = self.to_flat_dict().copy()
        result[XFORM_ID_STRING] = self.get_xform_id_string()
        return result


def xform_instance_to_dict(xml_str):
    parser = XFormInstanceParser(xml_str)
    return parser.to_dict()

def xform_instance_to_flat_dict(xml_str):
    parser = XFormInstanceParser(xml_str)
    return parser.to_flat_dict()

def parse_xform_instance(xml_str):
    parser = XFormInstanceParser(xml_str)
    return parser.get_flat_dict_with_attributes()
