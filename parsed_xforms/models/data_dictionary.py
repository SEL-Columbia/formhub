import json
from django.db import models
from xform_manager.models import XForm
from pyxform.builder import create_survey_element_from_json
from common_tags import XFORM_ID_STRING
from parsed_xforms.models import xform_instances

class DataDictionary(models.Model):
    xform = models.ForeignKey(XForm, related_name="data_dictionary")
    json = models.TextField()
    variable_names_json = models.TextField(default=u"{}")

    class Meta:
        app_label = "parsed_xforms"

    def set_survey_object(self):
        if not hasattr(self, "_survey"):
            self._survey = create_survey_element_from_json(self.json)

    def get_survey_object(self):
        self.set_survey_object()
        return self._survey

    def get_survey_elements(self):
        self.set_survey_object()
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

    def get_variable_name(self, abbreviated_xpath):
        """
        If the abbreviated_xpath has been renamed in
        self.variable_names_json return that new name, otherwise
        return the original abbreviated_xpath.
        """
        if not hasattr(self, "_variable_names"):
            self._variable_names = json.loads(self.variable_names_json)
            assert type(self._variable_names)==dict
        if abbreviated_xpath in self._variable_names and \
                self._variable_names[abbreviated_xpath]:
            return self._variable_names[abbreviated_xpath]
        return abbreviated_xpath

    def get_parsed_instances_from_mongo(self):
        id_string = self.xform.id_string
        match_id_string = {XFORM_ID_STRING : id_string}
        parsed_instances = \
            xform_instances.find(spec=match_id_string)
        return list(parsed_instances)

    def get_data_for_excel(self):
        return self.get_parsed_instances_from_mongo()

    def get_headers_for_excel(self):
        def unique_keys(data):
            s = set()
            for d in data:
                for k in d.keys():
                    s.add(k)
            return list(s)
        result = unique_keys(self.get_parsed_instances_from_mongo())
        result.sort(cmp=self.get_xpath_cmp())
        return result
