import os

from utils import node, SEP, CHOICE_PREFIX
from xls2json import ExcelReader
from survey_element import SurveyElement


class Question(SurveyElement):
    pass


class InputQuestion(Question):
    """
    This control string is the same for: strings, integers, decimals,
    dates, geopoints, barcodes ...
    """
    def xml_control(self):
        return node(u"input", ref=self.get_xpath(), *self.xml_label_and_hint())


class UploadQuestion(Question):
    def _get_media_type(self):
        return self.get_control_dict()[u"mediatype"]
        
    def xml_control(self):
        return node(
            u"upload",
            ref=self.get_xpath(),
            mediatype=self._get_media_type(),
            *self.xml_label_and_hint()
            )


class Option(SurveyElement):
    def __init__(self, *args, **kwargs):
        """
        This is a little hack here, I'm going to use an option's value
        as its name.
        """
        self._value = kwargs[u"value"]
        SurveyElement.__init__(self, name=self._value, text=kwargs[u"text"])
    
    def xml_value(self):
        return node(u"value", self._value)

    def xml(self):
        item = node(u"item")
        item.append(self.xml_label())
        item.append(self.xml_value())
        return item


class MultipleChoiceQuestion(Question):
    def __init__(self, *args, **kwargs):
        Question.__init__(self, *args, **kwargs)
        for option in kwargs[u'choices']:
            self._add_option(**option)
        
    def validate(self):
        return Question.validate(self)
        
    def _add_option(self, **kwargs):
        option = Option(**kwargs)
        self._add_element(option)

    def xml_control(self):
        assert self.get_bind_dict()[u"type"] in [u"select", u"select1"]
        result = node(
            self.get_bind_dict()[u"type"],
            {u"ref" : self.get_xpath()}
            )
        for n in self.xml_label_and_hint():
            result.append(n)
        for n in [o.xml() for o in self._elements]:
            result.append(n)                
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
