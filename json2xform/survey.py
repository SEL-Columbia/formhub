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
                     E.instance(self.xml_instance()),
                     *self.xml_bindings()
                     ),
                   ),
                 E(ns("h", "body"), *self.xml_control())
                 )

    def _setup_translations(self):
        self._translations = defaultdict(dict)
        for e in self.iter_children():
            translation_keys = e.get_translation_keys()
            for translation_key, text in [
                (translation_keys[u"label"], e.get_label()),
                (translation_keys[u"hint"], e.get_hint())
                ]:
                for lang in text.keys():
                    if translation_key in self._translations[lang]:
                        assert self._translations[lang][translation_key] == text[lang], "The labels for this translation key are inconsistent %(key)s %(label)s" % {"key" : translation_key, "label" : text[lang]}
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
            self._created.strftime("%Y%m%d")

    def xml_instance(self):
        result = Section.xml_instance(self)
        result.attrib[u"id"] = self.id_string()
        return result

    def to_xml(self):
        return etree.tostring(self.xml(), pretty_print=True)
    
    def __unicode__(self):
        return "<survey name='%s' element_count='%s'>" % (self.get_name(), len(self._children))
    
    def _setup_xpath_dictionary(self):
        self._xpath = {}
        for element in self.iter_children():
            if isinstance(element, Question) or isinstance(element, Section):
                if element.get_name() in self._xpath:
                    self._xpath[element.get_name()] = None
                else:
                    self._xpath[element.get_name()] = element.get_xpath()
        
    def _var_repl_function(self):
        """
        Given a dictionary of xpaths, return a function we can use to
        replace ${varname} with the xpath to varname.
        """
        def repl(matchobj):
            if matchobj.group(1) not in self._xpath:
                raise Exception("There is not survey element with this name.",
                                matchobj.group(1))
            return self._xpath[matchobj.group(1)]
        return repl

    def insert_xpaths(self, text):
        """
        Replace all instances of ${var} with the xpath to var.
        """
        bracketed_tag = r"\$\{(" + XFORM_TAG_REGEXP + r")\}"
        return re.sub(bracketed_tag, self._var_repl_function(), text)

    def print_xform_to_file(self, filename=""):
        if not filename: filename = self.id_string() + ".xml"
        fp = codecs.open(filename, mode="w", encoding="utf-8")
        fp.write(self.to_xml())
        fp.close()
        
    def instantiate(self):
        from json2xform.instance import SurveyInstance
        return SurveyInstance(self)
