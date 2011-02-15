"""
A Python script to convert excel files into JSON.
"""

from xlrd import open_workbook
import json
import re
import sys
import codecs

# the following are the three sheet names that this program expects
SURVEY_SHEET = u"survey"
CHOICES_SHEET = u"choices"
TYPES_SHEET = u"question types"

CHOICE_LIST_NAME = u"list name"
DICT_CHAR = u":"
MULTIPLE_CHOICE_DELIMITER = r"\s+from\s+"

TYPE = u"type"
CHOICES = u"choices"

class ExcelReader(object):
    def __init__(self, path):
        self._path = path
        self._dict = None
        self._step1()
        sheet_names = self._dict.keys()
        if len(sheet_names)==2 and SURVEY_SHEET in sheet_names and CHOICES_SHEET in sheet_names:
            self._fix_int_values()
            self._group_dictionaries()
            self._construct_choice_lists()
            self._insert_choice_lists()
        if sheet_names==[TYPES_SHEET]:
            self._group_dictionaries()
            self._dict = self._dict[TYPES_SHEET]

    def to_dict(self):
        return self._dict

    def print_json_to_file(self):
        fp = codecs.open(self._path[:-4] + ".json", mode="w", encoding="utf-8")
        json.dump(converter.to_dict(), fp=fp, ensure_ascii=False, indent=4)
        fp.close()

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
        choice_list = self._dict[CHOICES_SHEET]
        choices = {}
        for choice in choice_list:
            list_name = choice.pop(CHOICE_LIST_NAME)
            if list_name in choices: choices[list_name].append(choice)
            else: choices[list_name] = [choice]
        self._dict[CHOICES_SHEET] = choices

    def _insert_choice_lists(self):
        """
        For each multiple choice question in the survey find the
        corresponding list of choices and add it to that
        question. Finally, drop the choice lists and set the
        underlying dict to be just the survey definition.
        """
        for q in self._dict[SURVEY_SHEET]:
            l = re.split(MULTIPLE_CHOICE_DELIMITER, q[TYPE])
            if len(l) > 2: raise Exception("There should be at most one 'from' in a question type.")
            if len(l)==2:
                assert CHOICES not in q
                q[CHOICES] = self._dict[CHOICES_SHEET][l[1]]
                q[TYPE] = l[0]
        self._dict = self._dict[SURVEY_SHEET]

if __name__=="__main__":
    # Open the excel file that is the second argument to this python
    # call, convert that file to json and save that json to a file
    path = sys.argv[1]
    assert path[-4:]==".xls"
    converter = ExcelReader(path)
    converter.print_json_to_file()
    # print json.dumps(converter.to_dict(), ensure_ascii=False, indent=4)
