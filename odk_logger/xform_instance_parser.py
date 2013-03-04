from xml.dom import minidom, Node
import re
from django.utils.encoding import smart_unicode, smart_str
from django.utils.translation import ugettext_lazy, ugettext as _

XFORM_ID_STRING = u"_xform_id_string"


class XLSFormError(Exception):
    pass


class DuplicateInstance(Exception):
    def __unicode__(self):
        return _("Duplicate Instance")
    def __str__(self):
        return unicode(self).encode('utf-8')


class IsNotCrowdformError(Exception):
    def __unicode__(self):
        return _("The form is not a crowdform")
    def __str__(self):
        return unicode(self).encode('utf-8')


class InstanceInvalidUserError(Exception):
    def __unicode__(self):
        return _("Could not determine the user.")
    def __str__(self):
        return unicode(self).encode('utf-8')


class InstanceParseError(Exception):
    def __unicode__(self):
        return _("The instance could not be parsed.")
    def __str__(self):
        return unicode(self).encode('utf-8')


class InstanceEmptyError(InstanceParseError):
    def __unicode__(self):
        return _("Empty instance")
    def __str__(self):
        return unicode(self).encode('utf-8')


def get_meta_from_xml(xml_str, meta_name):
    xml = clean_and_parse_xml(xml_str)
    children = xml.childNodes
    # children ideally contains a single element that is the parent of all survey elements
    if children.length == 0:
        raise ValueError(_("XML string must have a survey element."))
    survey_node = children[0]
    meta_tags = [n for n in survey_node.childNodes if\
                 n.nodeType == Node.ELEMENT_NODE and n.tagName.lower() == "meta"]
    if len(meta_tags) == 0:
        return None

    # get the requested tag
    meta_tag = meta_tags[0]
    uuid_tags = [n for n in meta_tag.childNodes if\
                   n.nodeType == Node.ELEMENT_NODE and\
                   n.tagName.lower() == meta_name.lower()]
    if len(uuid_tags) == 0:
        return None

    uuid_tag = uuid_tags[0]
    return uuid_tag.firstChild.nodeValue.strip() if uuid_tag.firstChild\
        else None


def get_uuid_from_xml(xml):
    uuid = get_meta_from_xml(xml, "instanceID")
    regex = re.compile(r"uuid:(.*)")
    if uuid:
        matches = regex.match(uuid)
        if matches and len(matches.groups()) > 0:
            return matches.groups()[0]
    return None


def get_deprecated_uuid_from_xml(xml):
    uuid = get_meta_from_xml(xml, "deprecatedID")
    regex = re.compile(r"uuid:(.*)")
    if uuid:
        matches = regex.match(uuid)
        if matches and len(matches.groups()) > 0:
            return matches.groups()[0]
    return None


def clean_and_parse_xml(xml_string):
    clean_xml_str = xml_string.strip()
    clean_xml_str = re.sub(ur">\s+<", u"><", smart_unicode(clean_xml_str))
    xml_obj = minidom.parseString(smart_str(clean_xml_str))
    return xml_obj


def _xml_node_to_dict(node, repeats=[]):
    assert isinstance(node, minidom.Node)
    if len(node.childNodes) == 0:
        # there's no data for this leaf node
        return None
    elif len(node.childNodes) == 1 and \
            node.childNodes[0].nodeType == node.TEXT_NODE:
        # there is data for this leaf node
        return {node.nodeName: node.childNodes[0].nodeValue}
    else:
        # this is an internal node
        value = {}
        for child in node.childNodes:

            # handle CDATA text section
            if child.nodeType == child.CDATA_SECTION_NODE:
                return {child.parentNode.nodeName: child.nodeValue}

            d = _xml_node_to_dict(child, repeats)
            if d is None:
                continue
            child_name = child.nodeName
            child_xpath = xpath_from_xml_node(child)
            assert d.keys() == [child_name]
            node_type = dict
            # check if name is in list of repeats and make it a list if so
            if child_xpath in repeats:
                node_type = list

            if node_type == dict:
                if child_name not in value:
                    value[child_name] = d[child_name]
                else:
                    raise Exception((u"Multiple nodes with the same name '%s' while not a repeat" % child_name))
            else:
                if child_name not in value:
                    value[child_name] = [d[child_name]]
                else:
                    value[child_name].append(d[child_name])
        if value == {}:
            return None
        else:
            return {node.nodeName: value}


def _flatten_dict(d, prefix):
    """
    Return a list of XPath, value pairs.
    """
    assert type(d) == dict
    assert type(prefix) == list

    for key, value in d.items():
        new_prefix = prefix + [key]
        if type(value) == dict:
            for pair in _flatten_dict(value, new_prefix):
                yield pair
        elif type(value) == list:
            for i, item in enumerate(value):
                item_prefix = list(new_prefix)  # make a copy
                # note on indexing xpaths: IE5 and later has
                # implemented that [0] should be the first node, but
                # according to the W3C standard it should have been
                # [1]. I'm adding 1 to i to start at 1.
                if i > 0:
                    # hack: removing [1] index to be consistent across
                    # surveys that have a single repitition of the
                    # loop versus mutliple.
                    item_prefix[-1] += u"[%s]" % unicode(i + 1)
                if type(item) == dict:
                    for pair in _flatten_dict(item, item_prefix):
                        yield pair
                else:
                    yield (item_prefix, item)
        else:
            yield (new_prefix, value)


def _flatten_dict_nest_repeats(d, prefix):
    """
    Return a list of XPath, value pairs.
    """
    assert type(d) == dict
    assert type(prefix) == list

    for key, value in d.items():
        new_prefix = prefix + [key]
        if type(value) == dict:
            for pair in _flatten_dict_nest_repeats(value, new_prefix):
                yield pair
        elif type(value) == list:
            repeats = []
            for i, item in enumerate(value):
                item_prefix = list(new_prefix)  # make a copy
                if type(item) == dict:
                    repeat = {}
                    for path, value in _flatten_dict_nest_repeats(item, item_prefix):
                        #print "path: %s, value: %s" % (path, value)
                        #TODO: this only considers the first level of repeats
                        repeat.update({u"/".join(path[1:]): value})
                    repeats.append(repeat)
                else:
                    repeats.append({u"/".join(item_prefix[1:]): item})
            yield (new_prefix, repeats)
        else:
            yield (new_prefix, value)

def _gather_parent_node_list(node):
    node_names = []
    # also check for grand-parent node to skip document element
    if node.parentNode and node.parentNode.parentNode:
        node_names.extend(_gather_parent_node_list(node.parentNode))
    node_names.extend([node.nodeName])
    return node_names

def xpath_from_xml_node(node):
    node_names = _gather_parent_node_list(node)
    return "/".join(node_names[1:])


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

    def __init__(self, xml_str, data_dictionary):
        self.dd = data_dictionary
        self.parse(xml_str)

    def parse(self, xml_str):
        self._xml_obj = clean_and_parse_xml(xml_str)
        self._root_node = self._xml_obj.documentElement
        repeats = [e.get_abbreviated_xpath() for e in self.dd.get_survey_elements_of_type(u"repeat")]
        self._dict = _xml_node_to_dict(self._root_node, repeats)
        self._flat_dict = {}
        if self._dict is None:
            raise InstanceEmptyError
        for path, value in _flatten_dict_nest_repeats(self._dict, []):
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
            # commented since enketo forms may have the template attribute in multiple xml tags and I dont see the harm in overiding attributes at this point
            try:
                assert key not in self._attributes
            except AssertionError:
                import logging
                logger = logging.getLogger("console_logger")
                logger.debug("Skipping duplicate attribute: %s with value %s" % (key, value))
                logger.debug(str(all_attributes))
            else:
                self._attributes[key] = value

    def get_xform_id_string(self):
        return self._attributes[u"id"]

    def get_flat_dict_with_attributes(self):
        result = self.to_flat_dict().copy()
        result[XFORM_ID_STRING] = self.get_xform_id_string()
        return result


def xform_instance_to_dict(xml_str, data_dictionary):
    parser = XFormInstanceParser(xml_str, data_dictionary)
    return parser.to_dict()

def xform_instance_to_flat_dict(xml_str, data_dictionary):
    parser = XFormInstanceParser(xml_str, data_dictionary)
    return parser.to_flat_dict()

def parse_xform_instance(xml_str,data_dictionary):
    parser = XFormInstanceParser(xml_str, data_dictionary)
    return parser.get_flat_dict_with_attributes()
