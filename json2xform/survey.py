from .question import MultipleChoiceQuestion, create_question_from_dict
from .section import Section

import json

class Survey(Section):
    # def __init__(self, title):
    #     assert re.search(r"^" + XFORM_TAG_REGEXP + r"$", title)
    #     self.title = title
    #     self._stack = [self.title]
    #     self.questions = questions
    #     self._set_up_xpath_dictionary()
    #     self.created = datetime.now()

    def _set_up_xpath_dictionary(self):
        self.xpath = {}
        for q in self.questions:
            if q.name in self.xpath:
                raise Exception("Question names must be unique", q.name)
            self.xpath[q.name] = u"/" + self._stack[0] + u"/" + q.name

    def xml(self):
        return E(ns("h", "html"),
                 E(ns("h", "head"),
                   E(ns("h", "title"), self.title),
                   E("model",
                     E.itext(*self.translations()),
                     E.instance(self.instance()),
                     *self.bindings()
                     ),
                   ),
                 E(ns("h", "body"), *self.controls())
                 )

    def translations(self):
        dictionary = {}
        for q in self.questions:
            for k in q.text.keys():
                if k not in dictionary: dictionary[k] = []
                dictionary[k].append(
                    E.text(E.value(q.text[k]), id=SEP.join([QUESTION_PREFIX, q.name]))
                    )
            if isinstance(q, MultipleChoiceQuestion):
                for choice in q.choices:
                    for k in choice.text.keys():
                        if k not in dictionary: dictionary[k] = []
                        dictionary[k].append(
                            E.text(E.value(choice.text[k]), id=SEP.join([CHOICE_PREFIX, q.name, choice.value]))
                            )

        return [E.translation(lang=lang, *dictionary[lang]) for lang in dictionary.keys()]

    def id_string(self):
        return self.title + "_" + \
            self.created.strftime("%Y-%m-%d_%H-%M-%S")

    def instance(self):
        root_node_name = self._stack[0]
        result = E(root_node_name, {"id" : self.id_string()})
        for q in self.questions: result.append(q.instance())
        return result

    def bindings(self):
        # we need to calculate the xpaths of each question
        return [q.bind(self.xpath) for q in self.questions]

    def controls(self):
        return [q.control(self.xpath[q.name]) for q in self.questions]

    def __unicode__(self):
        return etree.tostring(self.xml(), pretty_print=True)
    
    def load_elements_from_json(self, json_text):
        element_dict_list = json.loads(json_text)
        for d in element_dict_list:
            q = create_question_from_dict(d)
            self._add_element(q)

    def _build_options_list_from_descendants(self):
        """
        used in preparation for exporting to XForm
        """
        self._options_list = []
        for element in self._elements:
            element.add_options_to_list(self._options_list)

        return self._options_list
