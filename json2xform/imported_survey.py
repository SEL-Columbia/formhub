#ImportedSurvey is separate from a normal SurveyObject because it doesn't have all the capabilities
#of a normal survey object (e.g. you can't add questions)
class ImportedSurvey(object):
    def __init__(self, **kwargs):
        """
        Accepts an xml document.
        
        Hopefully, it will parse the XML document and store a hint dict.
        """
        self._name = kwargs.get(u'name', "NoName")
        self._survey = kwargs.get(u'survey', None)
        self._label_hint_list = []
        if self._survey is not None:
            self._xml = kwargs.get(u'xml', self._survey.to_xml())
        else:
            self._xml = kwargs.get(u'xml')
        
        if self._xml is None:
            raise ImportSurveyError("No XML or Survey Provided for imported survey. %s" % self._name)
        self.parse_xml()
    
    def parse_xml(self):
        """
        1. Get keys from the xml instance.
        2. Find bindings from the bindings.
        3. Get the labels and hints that match up to those bindings.
        
        Will that work?
        """
        
    def instantiate(self):
        return Instance(imported_survey=self)
    
    def label_hint_list(self):
        return self._label_hint_list