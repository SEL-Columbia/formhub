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
    CHILDREN = u"children"

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
        for element in kwargs.get(u"children", []):
            self.add_child(element)

    def add_child(self, element):
        # I should probably rename this function, because now it handles lists
        if type(element)==list:
            for list_element in element:
                self.add_child(list_element)
        else:
            element._set_parent(self)
            self._children.append(element)

    def get(self, key):
        # name, type, control, bind, label, hint
        return self._dict[key]

    def set_name(self, name):
        self._dict[self.NAME] = name

    def validate(self):
        assert is_valid_xml_tag(self.get_name()), "%s is an invalid xml tag name" % self.get_name()
    
    def _set_parent(self, parent):
        self._parent = parent

    def iter_children(self):
        # it really seems like this method should not yield self
        yield self
        for e in self._children:
            for f in e.iter_children():
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
            u"label" : u"%s:label" % self.get_xpath(),
            u"hint" : u"%s:hint" % self.get_xpath(),
            }

    # XML generating functions, these probably need to be moved around.
    def xml_label(self):
        d = self.get_translation_keys()
        return node(u"label", ref="jr:itext('%s')" % d[u"label"])

    def xml_hint(self):
        d = self.get_translation_keys()
        return node(u"hint", ref="jr:itext('%s')" % d[u"hint"])

    def xml_label_and_hint(self):
        if self.get_hint():
            return [self.xml_label(), self.xml_hint()]
        return [self.xml_label()]

    def xml_binding(self):
        """
        Return the binding for this survey element.
        """
        survey = self.get_root()
        d = self.get_bind().copy()
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
        for e in self.iter_children():
            xml_binding = e.xml_binding()
            if xml_binding!=None: result.append(xml_binding)
        return result

    def xml_control(self):
        """
        The control depends on what type of question we're asking, it
        doesn't make sense to implement here in the base class.
        """
        raise Exception("Control not implemented")


# add a bunch of get methods to the SurveyElement class
def add_get_method(cls, key):
    def get_method(self):
        return self.get(key)
    get_method.__name__ = str("get_%s" % key)
    setattr(cls, get_method.__name__, get_method)

for key in SurveyElement._DEFAULT_VALUES.keys():
    add_get_method(SurveyElement, key)
