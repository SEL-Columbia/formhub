import os
from xls2json import ExcelReader
from . import utils

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

class SurveyElement(object):
    def __init__(self, *args, **kwargs):
        self._name = kwargs.get(u"name", "")
        self._attributes = kwargs.get(u"attributes", {})
        self._question_type = kwargs.get(u"question_type", None)

    def validate(self):
        assert utils.is_valid_xml_tag(self._name)
    
    def _set_parent(self, parent):
        self._parent = parent

    def to_dict(self):
        return {'name': self._name}

    def add_options_to_list(self, options_list):
        return options_list
        
    def _load_question_type_data(self, source):
        self._question_type_data = source

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

    # XML generating functions, these probably need to be moved around.
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


class Question(SurveyElement):
    pass


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


class Option(object):
    def __init__(self, **kwargs):
        self._value = kwargs[u'value']
        self._text = kwargs[u'text']
        object.__init__(self)
    
    def _set_parent(self, parent):
        self._parent = parent

    def __eq__(self, other):
        return other.to_dict()==self.to_dict()
        
    def to_dict(self):
        return {'value': self._value, 'text': self._text}

    def xml(self, question_name):
        return E.item(
            E.label(ref="jr:itext('%s')" % SEP.join([CHOICE_PREFIX, question_name, self.value])),
            E.value(self.value)
            )


class MultipleChoiceQuestion(Question):
    def __init__(self, *args, **kwargs):
        self._options = []
        if u'options' in kwargs:
            for option in kwargs[u'options']:
                self._add_option(**option)
        
        Question.__init__(self, *args, **kwargs)
    
    def add_options_to_list(self, options_list):
        if self._options not in options_list:
            options_list.append(self._options)
        self._option_list_index_number = options_list.index(self._options)

        return options_list
    
    
    def to_dict(self):
        base_dict = Question.to_dict(self)
        local_dict = {'options': [o.to_dict() for o in self._options] }
        return dict(base_dict.items() + local_dict.items())
    
    def validate(self):
        self._validate_unique_option_values()
        return Question.validate(self)
        
    def _validate_unique_option_values(self):
        option_values = []
        for option in self._options:
            if option._value in option_values:
                raise Exception("Option with value: '%s' already exists" % option._value)
            else:
                option_values.append(option._value)
    
    def _add_option(self, **kwargs):
        option = Option(**kwargs)
        option._set_parent(self)
        self._options.append(option)

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
