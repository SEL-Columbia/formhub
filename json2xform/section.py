from question import SurveyElement
from utils import node

class Section(SurveyElement):
    def validate(self):
        for element in self._children:
            element.validate()
        self._validate_uniqueness_of_element_names()

    # there's a stronger test of this when creating the xpath
    # dictionary for a survey.
    def _validate_uniqueness_of_element_names(self):
        element_slugs = []
        for element in self._children:
            if element.get_name() in element_slugs:
                raise Exception("Element with namme: '%s' already exists" % element.get_name())
            else:
                element_slugs.append(element.get_name())

    def xml_instance(self):
        result = node(self.get_name())
        for child in self._children:
            result.append(child.xml_instance())
        return result

    def xml_control(self):
        """
        Ideally, we'll have groups up and rolling soon, but for now
        let's just return a list of controls from all the children of
        this section.
        """
        return [e.xml_control() for e in self._children if e.xml_control() is not None]
