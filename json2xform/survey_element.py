import utils
from collections import defaultdict

class SurveyElement(object):
    def __init__(self, *args, **kwargs):
        self._name = kwargs.get(u"name", u"")
        self._text = kwargs.get(u"text", {})
        self._type = kwargs.get(u"type", u"")
        self._attributes = defaultdict(dict)
        self.set_attributes(kwargs.get(u"attributes", {}))
        self._parent = kwargs.get(u"parent", None)

    def get_control_dict(self):
        return self._attributes[u"control"]

    def get_bind_dict(self):
        return self._attributes[u"bind"]

    def validate(self):
        assert utils.is_valid_xml_tag(self._name)
    
    def _set_parent(self, parent):
        self._parent = parent
        
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
        return {'name': self._name}

    def add_options_to_list(self, options_list):
        pass
        
    def set_attributes(self, d):
        """
        This is a little hacky. I think it would be cleaner to use a
        meta class to create a new class for each question type.
        """
        self._attributes.update(d)

    # XML generating functions, these probably need to be moved around.
    def label_element(self):
        return utils.E.label(ref="jr:itext('%s')" % utils.SEP.join([utils.QUESTION_PREFIX, self._name]))

    def hint_element(self):
        # I need to fix this like label above
        if self.hint:
            return utils.E.hint(self.hint)

    def label_and_hint(self):
        # if self.hint:
        #     return [self.label_element(), self.hint_element()]
        return [self.label_element()]

    def instance(self):
        return utils.E(self._name)
    
    def get_bindings(self):
        """
        Return a list of XML nodes for the binding of this survey
        element and all its descendants. Note: we have to pass in a
        dictionary of xpaths to do xpath substitution here.
        """
        survey = self.get_root()
        d = dict([(k, survey.insert_xpaths(v)) for k, v in self._attributes.items()])
        return [ utils.E.bind(nodeset=self.get_xpath(), **d) ]

    def control(self):
        """
        The control depends on what type of question we're asking, it
        doesn't make sense to implement here in the base class.
        """
        raise Exception("Control not implemented")
