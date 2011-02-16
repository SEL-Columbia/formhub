from .question import MultipleChoiceQuestion, create_question_from_dict
from .section import Section
from .utils import E, ns, SEP, QUESTION_PREFIX, CHOICE_PREFIX, etree
from datetime import datetime
import codecs

import json

class Survey(Section):
    # def __init__(self, title):
    #     assert re.search(r"^" + XFORM_TAG_REGEXP + r"$", title)
    #     self.title = title
    #     self._stack = [self.title]
    #     self.questions = questions
    #     self._set_up_xpath_dictionary()
    def __init__(self, *args, **kwargs):
        self._xpath = {}
        self._parent = None
        self._created = datetime.now()
        Section.__init__(self, *args, **kwargs)

    def xml(self):
        """
        calls necessary preparation methods, then returns the xml.
        """
        self.validate()
        
        self._build_options_list_from_descendants()
        self._add_to_xpath_dictionary(element=self)
        
        return E(ns("h", "html"),
                 E(ns("h", "head"),
                   E(ns("h", "title"), self._name),
                   E("model",
                     E.itext(*self.translations()),
                     E.instance(self.instance()),
                     *self.get_bindings(self._xpath)
                     ),
                   ),
                 E(ns("h", "body"), *self.controls())
                 )

    def translations(self):
        dictionary = {}
        for q in self._elements:
            for k in q._text.keys():
                if k not in dictionary: dictionary[k] = []
                dictionary[k].append(
                    E.text(E.value(q._text[k]), id=SEP.join([QUESTION_PREFIX, q._name]))
                    )
            if isinstance(q, MultipleChoiceQuestion):
                for choice in q._options:
                    for k in choice._text.keys():
                        if k not in dictionary: dictionary[k] = []
                        dictionary[k].append(
                            E.text(E.value(choice._text[k]), id=SEP.join([CHOICE_PREFIX, q._name, choice.value]))
                            )

        return [E.translation(lang=lang, *dictionary[lang]) for lang in dictionary.keys()]

    def id_string(self):
        return self._name + "_" + \
            self._created.strftime("%Y-%m-%d_%H-%M-%S")

    # most of the instance and controls and bindings should be handled
    # in SurveyElement
    def instance(self):
        root_node_name = self._name
        result = E(root_node_name, {"id" : self.id_string()})
        for q in self._elements: result.append(q.instance())
        return result

    def controls(self):
        return [q.control() for q in self._elements]

    def to_xml(self):
        return etree.tostring(self.xml(), pretty_print=True)
    
    def __unicode__(self):
        return "<survey name='%s' element_count='%s'>" % (self._name, len(self._elements))
    
    def _build_options_list_from_descendants(self):
        """
        used in preparation for exporting to XForm. Returns the list so that we can test it.
        """
        self._options_list = []
        for element in self._elements:
            element.add_options_to_list(self._options_list)

        return self._options_list
    
    def _add_to_xpath_dictionary(self, element):
        """
        Adds this element and all its children to this survey's xpath
        dictionary.
        """
        if element._name in self._xpath:
            raise Exception("Survey element names must be unique", element._name)
        self._xpath[element._name] = element.get_xpath()
        if isinstance(element, Section):
            for e in self._elements:
                self._add_to_xpath_dictionary(e)
        
    def load_elements_from_json(self, text_or_path):
        """
        Called when importing from a json text file. This uses the
        create_question_from_dict method in question.py.
        """
        try:
            # right now I'm just going to assume text_or_path is a path
            fp = codecs.open(text_or_path, mode="r", encoding="utf-8")
            element_dict_list = json.load(fp, encoding="utf-8")
        except IOError:
            element_dict_list = json.loads(text_or_path)

        for d in element_dict_list:
            q = create_question_from_dict(d)
            self._add_element(q)
