import json
from django.db import models
from xform_manager.models import XForm
from pyxform.builder import create_survey_element_from_json

class DataDictionary(models.Model):
    xform = models.ForeignKey(XForm, related_name="data_dictionary")
    json = models.TextField()
    # rename_json = models.TextField(default=u"{}")

    class Meta:
        app_label = "parsed_xforms"

    def set_survey_object(self):
        if not hasattr(self, "_survey"):
            self._survey = create_survey_element_from_json(self.json)

    def get_survey_object(self):
        self.set_survey_object()
        return self._survey

    def get_survey_elements(self):
        return self._survey.iter_children()

    def get_label(self, abbreviated_xpath):
        if not hasattr(self, "_label_from_xpath"):
            self._label_from_xpath = {}
            for e in self.get_survey_elements():
                # todo: think about multiple language support
                self._label_from_xpath[e.get_abbreviated_xpath()] = \
                    e.get_label()
        return self._label_from_xpath.get(abbreviated_xpath, None)

    def get_xpath_cmp(self):
        self.set_survey_object()
        if not hasattr(self, "_xpaths"):
            self._xpaths = [e.get_abbreviated_xpath() for e in self.get_survey_elements()]
        def xpath_cmp(x, y):
            # For the moment, we aren't going to worry about repeating
            # nodes.
            if x not in self._xpaths and y not in self._xpaths:
                return 0
            elif x not in self._xpaths:
                return 1
            elif y not in self._xpaths:
                return -1
            return cmp(self._xpaths.index(x), self._xpaths.index(y))
        return xpath_cmp

    def sort_xpaths(self, xpaths):
        xpath_cmp = self.get_xpath_cmp()
        xpaths.sort(cmp=xpath_cmp)

    def get_variable_name(self, xpath):
        """
        If the xpath has been renamed in self.rename_json return that new name, otherwise return the original xpath.
        """
        # if not hasattr(self, "_rename_dictionary"):
        #     self._rename_dictionary = json.loads(self.rename_json)
        #     assert type(self._rename_dictionary)==dict
        # if xpath in self._rename_dictionary and self._rename_dictionary[xpath]:
        #     return self._rename_dictionary[xpath]
        return xpath
