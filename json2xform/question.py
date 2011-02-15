class XFormElement(object):
    def __init__(self, *args, **kwargs):
        self._name = kwargs.get(u"name", "")
        self._attributes = kwargs.get(u"attributes", {})
        self._question_type = kwargs.get(u"question_type", None)

    def validate(self):
        pass
    
    def _set_parent(self, parent):
        self._parent = parent

    def to_dict(self):
        return {'name': self._name}

    def add_options_to_list(self, options_list):
        return options_list
        
    def _load_question_type_data(self, source):
        self._question_type_data = source

class RootQuestion(XFormElement):
    pass

class MultipleChoiceQuestion(RootQuestion):
    def __init__(self, *args, **kwargs):
        self._options = []
        if u'options' in kwargs:
            for option in kwargs[u'options']:
                self._add_option(**option)
        
        RootQuestion.__init__(self, *args, **kwargs)
    
    def add_options_to_list(self, options_list):
        if self._options not in options_list:
            options_list.append(self._options)
        self._option_list_index_number = options_list.index(self._options)

        return options_list
    
    
    def to_dict(self):
        base_dict = RootQuestion.to_dict(self)
        local_dict = {'options': [o.to_dict() for o in self._options] }
        return dict(base_dict.items() + local_dict.items())
    
    def validate(self):
        self._validate_unique_option_values()
        return RootQuestion.validate(self)
        
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

class InputQuestion(RootQuestion):
    pass



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


from xls2json import ExcelReader
import os

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
    "" : RootQuestion,
    "input" : InputQuestion,
    "select" : MultipleChoiceQuestion,
    "select1" : MultipleChoiceQuestion,
    "upload" : RootQuestion,
    }

def get_question_from_dict(d):
    d_type = d.pop("type")
    question_type = question_types_by_name[d_type]
    question_class = question_classes[ question_type["control"].get("tag", "") ]
    
    #non-unicode strings fixes a problem with passing params to question_class
    #d={'text': {'French': 'Combien?', 'English': 'How many?'}, 'name': 'exchange_rate', 'question_type': 'decimal', 'attributes': {}}
    d[u'question_type'] = d_type
    
    question = question_class(**d)
    question._question_type_data = question_type
    
    return question

