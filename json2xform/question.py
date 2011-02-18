import os

import utils
from xls2json import ExcelReader
from survey_element import SurveyElement


class Question(SurveyElement):
    pass


class InputQuestion(Question):
    """
    This control string is the same for: strings, integers, decimals,
    dates, geopoints, barcodes ...
    """
    def control(self):
        return utils.E.input(ref=self.get_xpath(), *self.label_and_hint())


class UploadQuestion(Question):
    def _get_media_type(self):
        return self.get_control_dict()[u"mediatype"]
        
    def control(self):
        return utils.E.upload(
            ref=self.get_xpath(),
            mediatype=self._get_media_type(),
            *self.label_and_hint()
            )


# I'm thinking we probably want this to be a SurveyElement
class Option(SurveyElement):
    def __init__(self, *args, **kwargs):
        SurveyElement.__init__(
            self,
            name=kwargs[u'value'],
            text=kwargs[u'text']
            )
    
    def __eq__(self, other):
        return other.to_dict()==self.to_dict()
        
    def to_dict(self):
        return {'value': self._name, 'text': self._text}

    def get_translation_id(self):
        self._parent

    def xml(self, question_name):
        return utils.E.item(
            utils.E.label(ref="jr:itext('%s')" % utils.SEP.join([CHOICE_PREFIX, question_name, self._name])),
            utils.E.value(self._name)
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
            if option._name in option_values:
                raise Exception("Option with value: '%s' already exists" % option._value)
            else:
                option_values.append(option._name)
    
    def _add_option(self, **kwargs):
        option = Option(**kwargs)
        option._set_parent(self)
        self._options.append(option)

    def control(self):
        assert self.get_bind_dict()[u"type"] in [u"select", u"select1"]
        result = utils.E(self.get_bind_dict()[u"type"], {"ref" : self.get_xpath()})
        for element in self.label_and_hint() + [c.xml(self._name) for c in self._options]:
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

def create_question_from_dict(d):
    q_type_str = d.pop("type")
    if q_type_str.endswith(" or specify other"):
        q_type_str = q_type_str[:len(q_type_str)-len(" or specify other")]
    question_type = question_types_by_name[q_type_str]
    question_class = question_classes[ question_type["control"].get("tag", "") ]
    d[u'type'] = q_type_str
    
    #this is because of a python2.6 issue w unicode strings as keys.
    new_dict={}
    for key in d: new_dict[str(key)] = d[key]
    result = question_class(**new_dict)
    
    result.set_attributes(question_type)
    return result


# we will need to write a helper function to create tables of questions
# i'm thinking the excel syntax will look something like:
# begin table with columns from ...
# row1
# row2 ...
# end table
def table(rows, columns):
    result = []
    for row_text, row_name in tuples(rows):
        for d in columns:
            kwargs = d.copy()
            kwargs["text"] = row_text + u": " + kwargs["text"]
            kwargs["name"] = row_name + u" " + kwargs.get("name", sluggify(kwargs["text"]))
            result.append(q(**kwargs))
    return result
