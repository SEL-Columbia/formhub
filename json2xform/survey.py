from .question import MultipleChoiceQuestion, get_question_from_dict
from .section import Section

import json

class Survey(Section):
    def load_elements_from_json(self, json_text):
        element_dict_list = json.loads(json_text)
        for d in element_dict_list:
            q = get_question_from_dict(d)
            self._add_element(q)

    def _build_options_list_from_descendants(self):
        """
        used in preparation for exporting to XForm
        """
        self._options_list = []
        for element in self._elements:
            element.add_options_to_list(self._options_list)

        return self._options_list
    
