import os
from utils import node, SEP, CHOICE_PREFIX
from survey_element import SurveyElement
from xls2json import ExcelReader


class Question(SurveyElement):
    # this is a dictionary of all the question types we will use in creating XForms.
    _path_to_this_file = os.path.abspath(__file__)
    _path_to_this_dir = os.path.dirname(_path_to_this_file)
    _path_to_question_types = os.path.join(_path_to_this_dir, "question_types.xls")
    _excel_reader = ExcelReader(_path_to_question_types)
    TYPES = _excel_reader.to_dict()

    def get_bind_dict(self):
        """
        Overlay this questions binding attributes on type of the
        attributes from this question type.
        """
        question_type_dict = self.TYPES[ self.get_type() ]
        question_type_bind_dict = question_type_dict[self.BIND]
        result = question_type_bind_dict.copy()
        result.update( SurveyElement.get_bind_dict(self) )
        return result


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
    VALUE = u"value"

    def __init__(self, *args, **kwargs):
        """
        This is a little hack here, I'm going to use an option's value
        as its name.
        """
        d = {
            self.LABEL : kwargs[self.LABEL],
            self.NAME : kwargs[self.VALUE],
            }
        SurveyElement.__init__(self, **d)
        self._dict[self.VALUE] = kwargs[self.VALUE]

    def get_value(self):
        return self._dict[self.VALUE]
    
    def xml_value(self):
        return node(u"value", self.get_value())

    def xml(self):
        item = node(u"item")
        item.append(self.xml_label())
        item.append(self.xml_value())
        return item


class MultipleChoiceQuestion(Question):
    def __init__(self, *args, **kwargs):
        Question.__init__(self, *args, **kwargs)
        for option in kwargs.get(u'choices', []):
            self._add_option(**option)
        
    def validate(self):
        return Question.validate(self)
        
    def _add_option(self, **kwargs):
        option = Option(**kwargs)
        self.add_child(option)

    def xml_control(self):
        assert self.get_bind_dict()[u"type"] in [u"select", u"select1"]
        result = node(
            self.get_bind_dict()[u"type"],
            {u"ref" : self.get_xpath()}
            )
        for n in self.xml_label_and_hint():
            result.append(n)
        for n in [o.xml() for o in self._children]:
            result.append(n)                
        return result
