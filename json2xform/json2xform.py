# For creating an xform for ODK there are three components:
# Instance: which only needs the name of the question.
# Binding: which needs a bunch of attributes.
# Control: which is determined by the type of the question.

#        import ipdb; ipdb.set_trace()

import json, re
from datetime import datetime
from copy import copy
from lxml import etree
from lxml.builder import ElementMaker
import sys
from xls2json import ExcelReader
import os

nsmap = {
    None : "http://www.w3.org/2002/xforms",
    "h" : "http://www.w3.org/1999/xhtml",
    "ev" : "http://www.w3.org/2001/xml-events",
    "xsd" : "http://www.w3.org/2001/XMLSchema",
    "jr" : "http://openrosa.org/javarosa",
    }

E = ElementMaker(nsmap=nsmap)

QUESTION_PREFIX = "q"
CHOICE_PREFIX = "c"
SEP = "_"

# http://www.w3.org/TR/REC-xml/
TAG_START_CHAR = r"[a-zA-Z:_]"
TAG_CHAR = r"[a-zA-Z:_0-9\-\.]"
XFORM_TAG_REGEXP = "%(start)s%(char)s*" % {"start" : TAG_START_CHAR, "char" : TAG_CHAR}

def ns(abbrev, text):
    return "{" + nsmap[abbrev] + "}" + text

def sluggify(text, delimiter=SEP):
    return re.sub(ur"[^a-z]+", delimiter, text.lower())

def json_dumps(obj):
    def default_encode(obj):
        return obj.__dict__
    return json.dumps(obj, indent=4, default=default_encode)

def _var_repl_function(xpaths):
    """
    Given a dictionary of xpaths, return a function we can use to
    replace ${varname} with the xpath to varname.
    """
    return lambda matchobj: xpaths[matchobj.group(1)]

def insert_xpaths(xpaths, text):
    """
    Replace all instances of ${var} with the xpath to var.
    """
    bracketed_tag = r"\$\{(" + XFORM_TAG_REGEXP + r")\}"
    return re.sub(bracketed_tag, _var_repl_function(xpaths), text)

class Question(object):
    """
    Abstract base class to build different question types on top of.
    """
    def __init__(self, name, text, hint={}, attributes={}):
        assert re.search(r"^" + XFORM_TAG_REGEXP + r"$", name)
        self.name = name
        self.text = text
        self._attributes = attributes.copy()
        self.hint = hint

    def set_question_type(self, d):
        """
        This is a little hacky. I think it would be cleaner to use a
        meta class to create a new class for each question type.
        """
        for k, v in d["bind"].items():
            if ":" in k:
                # we need to handle namespacing of attributes
                l = k.split(":")
                assert len(l)==2
                k = ns(l[0], l[1])
            self._attributes[k] = v
        self.hint = d.get("hint", {})

    def label_element(self):
        return E.label(ref="jr:itext('%s')" % SEP.join([QUESTION_PREFIX, self.name]))

    def hint_element(self):
        # I need to fix this like label above
        if self.hint:
            return E.hint(self.hint)

    def label_and_hint(self):
        # if self.hint:
        #     return [self.label_element(), self.hint_element()]
        return [self.label_element()]

    def instance(self):
        return E(self.name)

    def bind(self):
        """
        Return an XML string representing the binding of this
        question.
        """
        d = dict([(k, insert_xpaths(xpaths, v)) for k, v in self._attributes.items()])
        return E.bind(nodeset=xpaths[self.name], **d)

    def control(self):
        """
        The control depends on what type of question we're asking, it
        doesn't make sense to implement here in the base class.
        """
        raise Exception("Control not implemented")

class InputQuestion(Question):
    """
    This control string is the same for: strings, integers, decimals,
    dates, geopoints, barcodes ...
    """
    def control(self):
        return E.input(ref=self.xpath(), *self.label_and_hint())

class UploadQuestion(Question):
    def control(self):
        return E.upload(ref=self.xpath(), mediatype=self.mediatype,
                        *self.label_and_hint())

class Choice(object):
    def __init__(self, value, text):
        self.value = unicode(value)
        self.text = text

    def xml(self, question_name):
        return E.item(
            E.label(ref="jr:itext('%s')" % SEP.join([CHOICE_PREFIX, question_name, self.value])),
            E.value(self.value)
            )

def choices(l):
    return [Choice(**d) for d in l]

class MultipleChoiceQuestion(Question):
    def __init__(self, **kwargs):
        """
        Multiple choice questions take two options not included in the
        base class: a list of choices, and a flag whether one can
        select one or many.
        """
        self.choices = choices(kwargs.pop("choices"))
        Question.__init__(self, **kwargs)

    def control(self):
        assert self._attributes[u"type"] in [u"select", u"select1"]
        result = E(self._attributes[u"type"], {"ref" : self.xpath()})
        for element in self.label_and_hint() + [c.xml(self.name) for c in self.choices]:
            result.append(element)
        return result        

# this is a list of all the question types we will use in creating XForms.
file_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "question_types.xls"
    )
question_types = ExcelReader(file_path).to_dict()

question_types_by_name = {}
for question_type in question_types:
    question_types_by_name[question_type.pop(u"name")] = question_type

question_classes = {
    "" : Question,
    "input" : InputQuestion,
    "select" : MultipleChoiceQuestion,
    "select1" : MultipleChoiceQuestion,
    "upload" : UploadQuestion,
    }

def q(d):
    question_type = question_types_by_name[d.pop("type")]
    question_class = question_classes[ question_type["control"].get("tag", "") ]
    result = question_class(**d)
    result.set_question_type(question_type)
    return result

# I haven't figured out how to put tables into Excel.
def table(rows, columns):
    result = []
    for row_text, row_name in tuples(rows):
        for d in columns:
            kwargs = d.copy()
            kwargs["text"] = row_text + u": " + kwargs["text"]
            kwargs["name"] = row_name + u" " + kwargs.get("name", sluggify(kwargs["text"]))
            result.append(q(**kwargs))
    return result

class Section(object):
    # name is the xml tag name in the instance
    # text is a dictionary of translations to label this group
    def __init__(self, name, text, elements=[]):
        self._elements = elements

class Survey(Section):
    def __init__(self, title):
        assert re.search(r"^" + XFORM_TAG_REGEXP + r"$", title)
        self.title = title
        self._stack = [self.title]
        self.questions = questions
        self._set_up_xpath_dictionary()
        self.created = datetime.now()

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




# def apply(function, survey):
#     l = len(survey.elements)
#     function(survey)
#     if len(survey.elements) > l:
#         apply(function, survey)

# def add_one_specify(survey):
#     for i in range(len(survey.elements)):
#         question = survey.elements[i]
#         if question.type in ["select one", "select all that apply"]:
#             if "other" in [choice[1] for choice in question.choices] and survey.elements[i+1].text!="Please specify":
#                 d = {"name" : question.name + " other",
#                      "text" : "Please specify",
#                      "type" : "string",
#                      "relevant" : "selected([%s], 'other')" % question.name}
#                 new_question = Question(**d)
#                 new_list = survey.elements[0:i+1]
#                 new_list.append(new_question)
#                 new_list.extend(survey.elements[i+1:len(survey.elements)])
#                 survey.elements = new_list
#                 return

# def main(path):
#     folder, filename = os.path.split(path)
#     m = re.search(r"([^\.]+)\.([^\.]+)$", filename)
#     filename = m.group(1).title()
#     title = m.group(1).title()
#     outfile = os.path.join("xforms", filename + ".xml")

#     survey = survey_from_text(path)
#     survey.title = title
#     apply(fake_one_table, survey)
#     apply(add_one_specify, survey)

#     f = open(outfile, "w")
#     xml_str = survey_to_xml(survey).encode("utf-8")
#     f.write(xml_str)
#     f.close()

def survey_from_json(path):
    f = open(path)
    questions = json.load(f)
    f.close()
    return Survey(title="Agriculture", questions=[q(d) for d in questions])

if __name__ == '__main__':
    s = survey_from_json(sys.argv[1])
    print s.__unicode__()
