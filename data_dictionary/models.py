from django.db import models
from xform_manager.models import XForm
from pyxform.builder import create_survey_element_from_json

class DataDictionary(models.Model):
    xform = models.ForeignKey(XForm)
    json = models.TextField()

    def set_survey_object(self):
        if not hasattr(self, "_survey"):
            self._survey = create_survey_element_from_json(self.json)

    def get_survey_object(self):
        self.set_survey_object()
        return self._survey

    def get_xpaths_and_labels(self):
        self.set_survey_object()
        if not hasattr(self, "_xpath_and_labels"):
            self._xpaths_and_labels = \
                [(e.get_abbreviated_xpath(), unicode(e.get_label())) for e in self._survey.iter_children()]
        return self._xpaths_and_labels

    def get_label(self, xpath):
        if not hasattr(self, "_label_from_xpath"):
            self._label_from_xpath = dict(self.get_xpaths_and_labels())
        return self._label_from_xpath.get(xpath, None)

    def get_xpath_cmp(self):
        self.set_survey_object()
        if not hasattr(self, "_xpaths"):
            self._xpaths = [e.get_abbreviated_xpath() for e in self._survey.iter_children()]
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

