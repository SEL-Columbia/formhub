import json
from django.db import models
from xform_manager.models import XForm
from pyxform import QuestionTypeDictionary, SurveyElementBuilder
from common_tags import XFORM_ID_STRING
from parsed_xforms.models import xform_instances
import re

class DataDictionary(models.Model):
    xform = models.ForeignKey(XForm, related_name="data_dictionary")
    json = models.TextField()
    variable_names_json = models.TextField(default=u"{}")

    class Meta:
        app_label = "parsed_xforms"

    def get_survey_object(self):
        if not hasattr(self, "_survey"):
            qtd = QuestionTypeDictionary("nigeria")
            builder = SurveyElementBuilder(question_type_dictionary=qtd)
            self._survey = builder.create_survey_element_from_json(self.json)
        return self._survey

    def get_survey_elements(self):
        return self.get_survey_object().iter_children()

    def get_element(self, abbreviated_xpath):
        if not hasattr(self, "_survey_elements"):
            self._survey_elements = {}
            for e in self.get_survey_elements():
                self._survey_elements[e.get_abbreviated_xpath()] = e
        return self._survey_elements.get(abbreviated_xpath)

    def get_label(self, abbreviated_xpath):
        e = self.get_element(abbreviated_xpath)
        # todo: think about multiple language support
        if e: return e.get_label()

    def remove_from_spreadsheet(self, abbreviated_xpath):
        # we will remove respondents 4 and above
        def respondent_index_above_two(abbreviated_xpath):
            m = re.search(r"^respondent\[(\d+)\]/", abbreviated_xpath)
            if m:
                return int(m.group(1)) > 3
            return False
        if respondent_index_above_two(abbreviated_xpath): return True
        e = self.get_element(abbreviated_xpath)
        if e is None: return False
        if e.get_bind().get(u"readonly")==u"true()":
            return True
        return False

    def get_xpath_cmp(self):
        if not hasattr(self, "_xpaths"):
            self._xpaths = [e.get_abbreviated_xpath() for e in self.get_survey_elements()]
        def xpath_cmp(x, y):
            # For the moment, we aren't going to worry about repeating
            # nodes.
            new_x = re.sub(r"\[\d+\]", u"", x)
            new_y = re.sub(r"\[\d+\]", u"", y)
            if new_x==new_y:
                return cmp(x, y)
            if new_x not in self._xpaths and new_y not in self._xpaths:
                return 0
            elif new_x not in self._xpaths:
                return 1
            elif new_y not in self._xpaths:
                return -1
            return cmp(self._xpaths.index(new_x), self._xpaths.index(new_y))
        return xpath_cmp

    def get_column_key_cmp(self):
        rename_hack = {
            u"state" : u"location/state_in_northwest",
            u"lga" : u"location/lga_in_jigawa"
            }
        xpath_cmp = self.get_xpath_cmp()
        def column_key_cmp(x, y):
            return xpath_cmp(rename_hack.get(x,x),
                             rename_hack.get(y,y))
        return column_key_cmp

    def _simple_get_variable_name(self, abbreviated_xpath):
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

    def get_variable_name(self, abbreviated_xpath):
        if self._rename_select_all_option_key(abbreviated_xpath):
            return self._rename_select_all_option_key(abbreviated_xpath)
        return self._simple_get_variable_name(abbreviated_xpath)

    def get_parsed_instances_from_mongo(self):
        id_string = self.xform.id_string
        match_id_string = {XFORM_ID_STRING : id_string}
        parsed_instances = \
            xform_instances.find(spec=match_id_string)
        return list(parsed_instances)

    def _rename_key(self, is_key_to_rename, new_key, data):
        for d in data:
            candidates = [k for k in d.keys() if is_key_to_rename(k)]
            for k in candidates:
                if d[k] is None:
                    del d[k]
                    candidates.remove(k)
            if len(candidates) > 1:
                for k in candidates:
                    del d[k]
            elif len(candidates)==1:
                assert new_key not in d
                d[new_key] = d[candidates[0]]
                del d[candidates[0]]

    def _collapse_other_into_select_one(self, data):
        for d in data:
            candidates = [k for k in d.keys() if k.endswith(u"_other")]
            for other_key in candidates:
                root_key = other_key[:-len(u"_other")]
                e = self.get_element(root_key)
                if e.get_bind().get(u"type")==u"select1":
                    if d[root_key]==u"other":
                        d[root_key] = d[other_key]
                    del d[other_key]

    def _expand_select_all_that_apply(self, data):
        def remove_all_indices(xpath):
            return re.sub(r"\[\d+\]", u"", xpath)
        for d in data:
            for key in d.keys():
                e = self.get_element(remove_all_indices(key))
                if e and e.get_bind().get(u"type")==u"select":
                    options_selected = None if d[key] is None else d[key].split()
                    for i, child in enumerate(e.get_children()):
                        new_key = key + u"[%s]" % i
                        if options_selected is None:
                            d[new_key] = u"n/a"
                        elif child.get_name() in options_selected:
                            assert new_key not in d
                            d[new_key] = True
                            if child.get_name()==u"other":
                                d[new_key] = d[key + u"_other"]
                                del d[key + u"_other"]
                        else:
                            d[new_key] = False
                    del d[key]

    def _rename_select_all_option_key(self, hacky_name):
        """
        hacky_name is the abbreviated xpath to the select all that
        apply question with an index appended to the end indicating
        the index of this child.
        """
        m = re.search(r"^(.+)\[(\d+)\]$", hacky_name)
        if m:
            e = self.get_element(m.group(1))
            if e and e.get_bind().get(u"type")==u"select":
                child = e.get_children()[int(m.group(2))]
                return self._simple_get_variable_name(m.group(1)) + \
                    u"_" + child.get_name()
        return None

    def _remove_index_from_first_instance_of_repeat(self, data):
        for d in data:
            candidates = [k for k in d.keys() if u"[1]" in k]
            for key in candidates:
                new_key = re.sub(r"\[1\]", "", key)
                assert new_key not in d
                d[new_key] = d[key]
                del d[key]

    def get_data_for_excel(self):
        result = self.get_parsed_instances_from_mongo()
        self._collapse_other_into_select_one(result)
        self._remove_index_from_first_instance_of_repeat(result)
        self._rename_key(lambda x: x.startswith(u"location/state_in_"), u"state", result)
        self._rename_key(lambda x: x.startswith(u"location/lga_in_"), u"lga", result)
        self._expand_select_all_that_apply(result)
        return result

    def get_column_keys_for_excel(self):
        def unique_keys(data):
            s = set()
            for d in data:
                for k in d.keys():
                    s.add(k)
            return list(s)
        result = unique_keys(self.get_data_for_excel())
        result.sort(cmp=self.get_column_key_cmp())
        return [key for key in result if not self.remove_from_spreadsheet(key)]
