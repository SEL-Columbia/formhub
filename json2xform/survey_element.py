from utils import is_valid_xml_tag, node, ns
from collections import defaultdict

class SurveyElement(object):
    # the following are important keys for the underlying dict that
    # describes this survey element
    NAME = u"name"
    LABEL = u"label"
    HINT = u"hint"
    TYPE = u"type"
    BIND = u"bind"
    CONTROL = u"control"
    # this node will also have a parent and children, like a tree!
    # these will not be stored in the dict.
    PARENT = u"parent"
    CHILDREN = u"elements"

    _DEFAULT_VALUES = {
        NAME : u"",
        LABEL : {},
        HINT : {},
        TYPE : u"",
        BIND : {},
        CONTROL : {},
        }

    def __init__(self, *args, **kwargs):
        self._dict = defaultdict(dict)
        for k, default_value in self._DEFAULT_VALUES.items():
            self._dict[k] = kwargs.get(k, default_value)
        self._parent = kwargs.get(u"parent", None)
        self._children = []
        for element in kwargs.get(u"elements", []):
            self.add_child(element)

    def add_child(self, element):
        element._set_parent(self)
        self._children.append(element)

    def get_name(self):
        return self._dict[self.NAME]

    def set_name(self, name):
        self._dict[self.NAME] = name

    def get_type(self):
        return self._dict[self.TYPE]
    
    def get_control_dict(self):
        return self._dict[self.CONTROL]

    def get_bind_dict(self):
        return self._dict[self.BIND]

    def get_label_dict(self):
        return self._dict[self.LABEL]

    def get_hint_dict(self):
        return self._dict[self.HINT]

    def validate(self):
        assert is_valid_xml_tag(self._dict[self.NAME])
    
    def _set_parent(self, parent):
        self._parent = parent

    def iter_elements(self):
        yield self
        for e in self._children:
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
        return u"/".join([u""] + [n.get_name() for n in self.get_lineage()])

    def to_dict(self):
        self.validate()
        result = dict([(k, v) for k, v in self._dict.items()])
        assert u"children" not in result
        result[u"children"] = [e.to_dict() for e in self._children]
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
            u"label" : u"%s:label" % self.get_name(),
            u"hint" : u"%s:hint" % self.get_name(),
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
        return node(self.get_name())
    
    def xml_binding(self):
        """
        Return the binding for this survey element.
        """
        survey = self.get_root()
        d = self.get_bind_dict().copy()
        if d:
            for k, v in d.items():
                d[k] = survey.insert_xpaths(v)
                if u":" in k:
                    l = k.split(u":")
                    assert len(l)==2
                    d[ns(l[0], l[1])] = survey.insert_xpaths(v)
                    del d[k]
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
