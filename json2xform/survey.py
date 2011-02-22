from question import MultipleChoiceQuestion
from section import Section
from question import Question
from utils import E, ns, SEP, QUESTION_PREFIX, CHOICE_PREFIX, etree, XFORM_TAG_REGEXP
from datetime import datetime
from collections import defaultdict
import codecs
import re
import json

class Survey(Section):
    def __init__(self, *args, **kwargs):
        Section.__init__(self, *args, **kwargs)
        self._xpath = {}
        self._parent = None
        self._created = datetime.now()

    def xml(self):
        """
        calls necessary preparation methods, then returns the xml.
        """
        self.validate()
        self._setup_xpath_dictionary()
        
        return E(ns("h", "html"),
                 E(ns("h", "head"),
                   E(ns("h", "title"), self.get_name()),
                   E("model",
                     E.itext(*self.xml_translations()),
                     E.instance(self.instance()),
                     *self.xml_bindings()
                     ),
                   ),
                 E(ns("h", "body"), *self.xml_control())
                 )

    def _setup_translations(self):
        self._translations = defaultdict(dict)
        for e in self.iter_elements():
            translation_keys = e.get_translation_keys()
            for translation_key, text in [
                (translation_keys[u"label"], e.get_label_dict()),
                (translation_keys[u"hint"], e.get_hint_dict())
                ]:
                for lang in text.keys():
                    if translation_key in self._translations[lang]:
                        assert self._translations[lang][translation_key] == text[lang], text
                    else:
                        self._translations[lang][translation_key] = text[lang]

    def xml_translations(self):
        self._setup_translations()
        result = []
        for lang in self._translations.keys():
            result.append( E.translation(lang=lang) )
            for name in self._translations[lang].keys():
                result[-1].append(
                    E.text(
                        E.value(self._translations[lang][name]),
                        id=name
                        )
                    )
        return result

    def id_string(self):
        return self.get_name() + "_" + \
            self._created.strftime("%Y-%m-%d_%H-%M-%S")

    # most of the instance and controls and bindings should be handled
    # in SurveyElement
    def instance(self):
        root_node_name = self.get_name()
        result = E(root_node_name, {u"id" : self.id_string()})
        for q in self._children: result.append(q.instance())
        return result

    def to_xml(self):
        return etree.tostring(self.xml(), pretty_print=True)
    
    def __unicode__(self):
        return "<survey name='%s' element_count='%s'>" % (self.get_name(), len(self._children))
    
    def _setup_xpath_dictionary(self):
        for element in self.iter_elements():
            if isinstance(element, Question) or isinstance(element, Section):
                if element.get_name() in self._xpath:
                    raise Exception("Survey element names must be unique", element.get_name())
                self._xpath[element.get_name()] = element.get_xpath()
        
    def _var_repl_function(self):
        """
        Given a dictionary of xpaths, return a function we can use to
        replace ${varname} with the xpath to varname.
        """
        return lambda matchobj: self._xpath[matchobj.group(1)]

    def insert_xpaths(self, text):
        """
        Replace all instances of ${var} with the xpath to var.
        """
        bracketed_tag = r"\$\{(" + XFORM_TAG_REGEXP + r")\}"
        return re.sub(bracketed_tag, self._var_repl_function(), text)
