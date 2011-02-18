from question import SurveyElement

class Section(SurveyElement):
    def __init__(self, *args, **kwargs):
        self._elements = []
        for element in kwargs.get(u"elements", []):
            self._add_element(element)
        SurveyElement.__init__(self, *args, **kwargs)
    
    def _add_element(self, element):
        element._set_parent(self)
        self._elements.append(element)
    
    def to_dict(self):
        """
        Finished product.
        NEEDS VALIDATION
        """
        self.validate()
        return {'name': self._name, 'elements': [e.to_dict() for e in self._elements]}

    def validate(self):
        for element in self._elements:
            element.validate()
        self._validate_uniqueness_of_element_names()

    # there's a stronger test of this when creating the xpath
    # dictionary for a survey.
    def _validate_uniqueness_of_element_names(self):
        element_slugs = []
        for element in self._elements:
            if element._name in element_slugs:
                raise Exception("Element with namme: '%s' already exists" % element._name)
            else:
                element_slugs.append(element._name)
