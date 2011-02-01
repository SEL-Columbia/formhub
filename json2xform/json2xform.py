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

    def bind(self, xpaths):
        """
        Return an XML string representing the binding of this
        question.
        """
        d = dict([(k, insert_xpaths(xpaths, v)) for k, v in self._attributes.items()])
        return E.bind(nodeset=xpaths[self.name], **d)

    def control(self, xpath):
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
    def control(self, xpath):
        return E.input(ref=xpath, *self.label_and_hint())

# The following code extends the class InputQuestion for a bunch of
# different types of InputQuestions.
def init_method(t):
    def __init__(self, **kwargs):
        InputQuestion.__init__(self, **kwargs)
        self._attributes[u"type"] = t
    return __init__

types = {
    "String" : u"string",
    "Integer" : u"int",
    "Geopoint" : u"geopoint",
    "Decimal" : u"decimal",
    "Date" : u"date",
    "Barcode" : u"barcode",
    }

for k, v in types.items():
    globals()[k + "Question"] = type(
        k + "Question",
        (InputQuestion,),
        {"__init__" : init_method(v)}
        )

# StringQuestion is on the classes we created above.
class Note(StringQuestion):
    def __init__(self, **kwargs):
        StringQuestion.__init__(self, **kwargs)
        self._attributes[u"readonly"] = u"true()"
        self._attributes[u"required"] = u"false()"

class PhoneNumberQuestion(StringQuestion):    
    def __init__(self, **kwargs):
        StringQuestion.__init__(self, **kwargs)
        self._attributes[u"constraint"] = u"regex(., '^\d*$')"
        # this approach to constrain messages doesn't work with lxml,
        # need to figure out how to do the name space thing correctly.
        # self._attributes[u"jr:constraintMsg"] = u"Please enter only numbers."
        self.hint = u"'0' = respondent has no phone number\n" + \
            u"'1' = respondent prefers to skip this question."

class PercentageQuestion(IntegerQuestion):
    def __init__(self, **kwargs):
        IntegerQuestion.__init__(self, **kwargs)
        self._attributes[u"constraint"] = u"0 <= . and . <= 100"
        self._attributes[u"jr:constraintMsg"] = \
            u"Please enter an integer between zero and one hundred."

class UploadQuestion(Question):
    def __init__(self, **kwargs):
        Question.__init__(self, **kwargs)
        self._attributes[u"type"] = u"binary"

    def control(self, xpath, mediatype):
        return E.upload(ref=xpath, mediatype=mediatype,
                        *self.label_and_hint())


class PictureQuestion(UploadQuestion):
    def control(self, xpath):
        return UploadQuestion.control(self, xpath, "image/*")

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

    def control(self, xpath):
        result = E(self._attributes[u"type"], {"ref" : xpath})
        for element in self.label_and_hint() + [c.xml(self.name) for c in self.choices]:
            result.append(element)
        return result        

class SelectOneQuestion(MultipleChoiceQuestion):
    def __init__(self, **kwargs):
        MultipleChoiceQuestion.__init__(self, **kwargs)
        self._attributes[u"type"] = u"select1"
        self.hint = u"select one"

class YesNoQuestion(SelectOneQuestion):
    def __init__(self, **kwargs):
        SelectOneQuestion.__init__(self, **kwargs)
        self.choices = choices([u"Yes", u"No"])

class YesNoDontKnowQuestion(SelectOneQuestion):
    def __init__(self, **kwargs):
        SelectOneQuestion.__init__(self, **kwargs)
        self.choices = choices([u"Yes", u"No", (u"Don't Know", u"unknown")])

class SelectMultipleQuestion(MultipleChoiceQuestion):
    def __init__(self, **kwargs):
        MultipleChoiceQuestion.__init__(self, **kwargs)
        self._attributes[u"type"] = u"select"
        self._attributes[u"required"] = u"false()"
        self.hint = u"select all that apply"

# Ideally, I'd like to make a bunch of functions with the prefix q and
# the rest of the function name is the question type. I'll look into
# this when I have Internet
question_class = {
    "string" : StringQuestion,
    "gps" : GeopointQuestion,
    "phone number" : PhoneNumberQuestion,
    "integer" : IntegerQuestion,
    "decimal" : DecimalQuestion,
    "percentage" : PercentageQuestion,
    "select one" : SelectOneQuestion,
    "select all that apply" : SelectMultipleQuestion,
    "yes or no" : YesNoQuestion,
    "date" : DateQuestion,
}
def q(d):
    c = question_class[d.pop("type")]
    return c(**d)

def table(rows, columns):
    result = []
    for row_text, row_name in tuples(rows):
        for d in columns:
            kwargs = d.copy()
            kwargs["text"] = row_text + u": " + kwargs["text"]
            kwargs["name"] = row_name + u" " + kwargs.get("name", sluggify(kwargs["text"]))
            result.append(q(**kwargs))
    return result    

class Survey(object):
    def __init__(self, title, questions):
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




#         "dateTime" : ["date and time"],

#     supported_attributes = ["required", "relevant", "readonly", "constraint", "jr:constraintMsg","jr:preload","jr:preloadParams", "calculate"]

# jr:preload questions dont have any control

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
