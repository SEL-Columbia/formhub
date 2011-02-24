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
CHOICES_SHEET = u"choices and columns"
COLUMNS_SHEET = u"columns"
TYPES_SHEET = u"question types"

CHOICE_LIST_NAME = u"list name"
DICT_CHAR = u":"

TYPE = u"type"
CHOICES = u"choices"

class ExcelReader(object):
    def __init__(self, path):
        self._path = path
        name_match = re.search(r"(?P<name>[^/]+)\.xls$", path)
        self._name = name_match.groupdict()["name"]
        self._dict = None
        self._setup()
        sheet_names = self._dict.keys()
        if SURVEY_SHEET in sheet_names:
            self._fix_int_values()
            self._group_dictionaries()
            self._process_question_type()
            if CHOICES_SHEET in sheet_names:
                self._construct_choice_lists()
                self._insert_choice_lists()
            self._dict = self._dict[SURVEY_SHEET]
            self._organize_sections()
        elif sheet_names==[TYPES_SHEET]:
            self._group_dictionaries()
            self._dict = self._dict[TYPES_SHEET]
            self._organize_by_type_name()

    def to_dict(self):
        return self._dict

    def print_json_to_file(self, filename=""):
        if not filename: filename = self._path[:-4] + ".json"
        fp = codecs.open(filename, mode="w", encoding="utf-8")
        json.dump(self.to_dict(), fp=fp, ensure_ascii=False, indent=4)
        fp.close()

    def _setup(self):
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

    def _process_question_type(self):
        """
        We need to handle question types that look like "select one
        from list-name or specify other.

        select one from list-name
        select all that apply from list-name
        select one from list-name or specify other
        select all that apply from list-name or specify other

        let's make it a requirement that list-names have no spaces
        """
        for q in self._dict[SURVEY_SHEET]:
            if TYPE not in q: raise Exception("Did not specify question type", q)
            question_type = q[TYPE]
            question_type.strip()
            re.sub(r"\s+", " ", question_type)
            if question_type.startswith(u"select"):
                m = re.search(r"^(?P<select_command>select one|select all that apply) from (?P<list_name>\S+)( (?P<specify_other>or specify other))?$", question_type)
                assert m, "unsupported select syntax:" + question_type
                assert CHOICES not in q
                d = m.groupdict()
                q[CHOICES] = d["list_name"]
                if d["specify_other"]:
                    q[TYPE] = " ".join([d["select_command"], d["specify_other"]])
                else:
                    q[TYPE] = d["select_command"]

    def _insert_choice_lists(self):
        """
        For each multiple choice question in the survey find the
        corresponding list of choices and add it to that
        question. Finally, drop the choice lists and set the
        underlying dict to be just the survey definition.
        """
        for q in self._dict[SURVEY_SHEET]:
            if CHOICES in q:
                q[CHOICES] = self._dict[CHOICES_SHEET][q[CHOICES]]

    def _organize_sections(self):
        # this needs to happen after columns have been inserted
        result = {u"type" : u"survey", u"name" : self._name, u"children" : []}
        stack = [result]
        for cmd in self._dict:
            cmd_type = cmd[u"type"]
            match_begin = re.match(r"begin (?P<type>group|repeat|table)", cmd_type)
            match_end = re.match(r"end (?P<type>group|repeat|table)", cmd_type)
            if match_begin:
                # start a new section
                cmd[u"type"] = match_begin.group(1)
                cmd[u"children"] = []
                stack[-1][u"children"].append(cmd)
                stack.append(cmd)
            elif match_end:
                begin_cmd = stack.pop()
                assert begin_cmd[u"type"] == match_end.group(1)
            else:
                stack[-1][u"children"].append(cmd)
        self._dict = result

    def _organize_by_type_name(self):
        result = {}
        for question_type in self._dict:
            result[question_type.pop(u"name")] = question_type
        self._dict = result

if __name__=="__main__":
    # Open the excel file that is the second argument to this python
    # call, convert that file to json and save that json to a file
    path = sys.argv[1]
    assert path[-4:]==".xls"
    converter = ExcelReader(path)
    # converter.print_json_to_file()
    print json.dumps(converter.to_dict(), ensure_ascii=False, indent=4)
