from question import SurveyElement

class Section(SurveyElement):
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

    def xml_control(self):
        """
        Ideally, we'll have groups up and rolling soon, but for now
        let's just return a list of controls from all the children of
        this section.
        """
        return [e.xml_control() for e in self._elements]
