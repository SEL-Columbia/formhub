from utils import is_valid_xml_tag, node
from collections import defaultdict

class SurveyElement(object):
    def __init__(self, *args, **kwargs):
        self._name = kwargs.get(u"name", u"")
        self._text = kwargs.get(u"text", {})
        self._type = kwargs.get(u"type", u"")
        self._attributes = defaultdict(dict)
        self.set_attributes(kwargs.get(u"attributes", {}))
        self._parent = kwargs.get(u"parent", None)
        self._elements = []
        for element in kwargs.get(u"elements", []):
            self._add_element(element)

    def _add_element(self, element):
        element._set_parent(self)
        self._elements.append(element)
    
    def get_control_dict(self):
        return self._attributes[u"control"]

    def get_bind_dict(self):
        return self._attributes[u"bind"]

    def get_label_dict(self):
        return self._text

    def get_hint_dict(self):
        return self._attributes[u"hint"]

    def validate(self):
        assert is_valid_xml_tag(self._name)
    
    def _set_parent(self, parent):
        self._parent = parent

    def iter_elements(self):
        yield self
        for e in self._elements:
            for f in e.iter_elements():
                yield f
        
    def get_lineage(self):
        """
        Return a the list [root, ..., self._parent, self]
        """
        result = [self]
        current_element = self
        while current_element._parent:
            current_element = current_element._parent
            result = [current_element] + result
        return result

    def get_root(self):
        return self.get_lineage()[0]

    def get_xpath(self):
        """
        Return the xpath of this survey element.
        """
        return u"/".join([u""] + [n._name for n in self.get_lineage()])

    def to_dict(self):
        self.validate()
        result = {
            u"name" : self._name,
            u"text" : self._text,
            u"type" : self._type,
            u"attributes" : self._attributes,
            u"children" : [e.to_dict() for e in self._elements]
            }
        # remove any keys with empty values
        for k, v in result.items():
            if not v: del result[k]
        return result

    def set_attributes(self, d):
        """
        This is a little hacky. I think it would be cleaner to use a
        meta class to create a new class for each question type.
        """
        self._attributes.update(d)

    def get_translation_keys(self):
        # we could base this off of the xpath instead of just the name
        return {
            u"label" : u"%s:label" % self._name,
            u"hint" : u"%s:hint" % self._name,
            }

    # XML generating functions, these probably need to be moved around.
    def xml_label(self):
        d = self.get_translation_keys()
        return node(u"label", ref="jr:itext('%s')" % d[u"label"])

    def xml_hint(self):
        d = self.get_translation_keys()
        return node(u"hint", ref="jr:itext('%s')" % d[u"hint"])

    def xml_label_and_hint(self):
        if self.get_hint_dict():
            return [self.xml_label(), self.xml_hint()]
        return [self.xml_label()]

    def instance(self):
        return node(self._name)
    
    def xml_binding(self):
        """
        Return the binding for this survey element.
        """
        survey = self.get_root()
        d = self.get_bind_dict().copy()
        if d:
            for k, v in d.items():
                d[k] = survey.insert_xpaths(v)
            return node(u"bind", nodeset=self.get_xpath(), **d)
        return None

    def xml_bindings(self):
        """
        Return a list of bindings for this node and all its descendents.
        """
        result = []
        for e in self.iter_elements():
            xml_binding = e.xml_binding()
            if xml_binding!=None: result.append(xml_binding)
        return result

    def xml_control(self):
        """
        The control depends on what type of question we're asking, it
        doesn't make sense to implement here in the base class.
        """
        raise Exception("Control not implemented")
