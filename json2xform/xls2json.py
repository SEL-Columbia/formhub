"""
A Python script to convert excel files into JSON.
"""

from xlrd import open_workbook
import json
import re
import sys

SURVEY = u"survey"
CHOICES = u"choices"
CHOICE_LIST_NAME = u"list name"
DICT_CHAR = u":"
TYPE = u"type"
QUESTION_TYPES = u"question types"
MULTIPLE_CHOICE_DELIMITER = r"\s+from\s+"
ATTRIBUTES = u"attributes"
RESERVED_FIELDS = [ATTRIBUTES, CHOICE_LIST_NAME, u"name", u"text", u"hint"]

class ExcelToJsonConverter(object):
    def __init__(self, path):
        self._path = path
        self._dict = None
        self._step1()
        sheet_names = self._dict.keys()
        if len(sheet_names)==2 and SURVEY in sheet_names and CHOICES in sheet_names:
            self._fix_int_values()
            self._group_dictionaries()
            self._construct_choice_lists()
            self._split_multiple_choice_types()
        if sheet_names==[QUESTION_TYPES]:
            self._group_dictionaries()

    def to_dict(self):
        return self._dict

    def get_json(self):
        return json.dumps(self._dict, indent=4)

    def _step1(self):
        """
        Return a Python dictionary with a key for each worksheet
        name. For each sheet there is a list of dictionaries, each
        dictionary corresponds to a single row in the worksheet. A
        dictionary has keys taken from the column headers and values
        equal to the cell value for that row and column.
        """
        workbook = open_workbook(self._path)
        self._dict = {}
        for sheet in workbook.sheets():
            self._dict[sheet.name] = []
            for row in range(1,sheet.nrows):
                row_dict = {}
                for column in range(0,sheet.ncols):
                    key = sheet.cell(0,column).value
                    value = sheet.cell(row,column).value
                    if value:
                        row_dict[key] = value
                if row_dict: self._dict[sheet.name].append(row_dict)

    def _fix_int_values(self):
        """
        Excel only has floats, but we really want integer values to be
        ints.
        """
        for sheet_name, dicts in self._dict.items():
            for d in dicts:
                for k, v in d.items():
                    if type(v)==float and v==int(v):
                        d[k] = int(v)

    def _group_dictionaries(self):
        """
        For each row in the worksheet, group all keys that contain a
        colon. So {"text:english" : "hello", "text:french" :
        "bonjour"} becomes {"text" : {"english" : "hello", "french" :
        "bonjour"}.
        """
        for sheet_name, dicts in self._dict.items():
            for d in dicts:
                groups = {}
                for k, v in d.items():
                    l = k.split(DICT_CHAR)
                    if len(l)>=2:
                        if l[0] not in groups:
                            groups[l[0]] = {}
                        groups[l[0]][DICT_CHAR.join(l[1:])] = v
                        del d[k]
                for k, v in groups.items():
                    assert k not in d
                    d[k] = v

    def _construct_choice_lists(self):
        """
        Each choice has a list name associated with it. Go through the
        list of choices, grouping all the choices by their list name.
        """
        choice_list = self._dict[CHOICES]
        choices = {}
        for choice in choice_list:
            list_name = choice.pop(CHOICE_LIST_NAME)
            if list_name in choices: choices[list_name].append(choice)
            else: choices[list_name] = [choice]
        self._dict[CHOICES] = choices

    def _split_multiple_choice_types(self):
        """
        For each multiple choice question in the survey break up the
        question type into two fields, one the multiple question type,
        two the list name that we're selecting from.
        """
        for q in self._dict[SURVEY]:
            l = re.split(MULTIPLE_CHOICE_DELIMITER, q[TYPE])
            if len(l) > 2: raise Exception("There should be at most one 'from' in a question type.")
            if len(l)==2:
                assert CHOICE_LIST_NAME not in q
                q[CHOICE_LIST_NAME] = l[1]
                q[TYPE] = l[0]

if __name__=="__main__":
    # Open the excel file that is the second argument to this python
    # call, convert that file to json and save that json to a file
    path = sys.argv[1]
    assert path[-4:]==".xls"
    converter = ExcelToJsonConverter(path)
    print converter.get_json()
    # f = open(path[:-4] + ".json", "w")
    # f.write(converter.get_json())
    # f.close()
