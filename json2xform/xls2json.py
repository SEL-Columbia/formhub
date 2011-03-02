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
CHOICES_SHEET_NAMES = [u"choices", u"choices and columns"]
COLUMNS_SHEET = u"columns"
TYPES_SHEET = u"question types"

LIST_NAME = u"list name"
DICT_CHAR = u":"

TYPE = u"type"
CHOICES = u"choices"
COLUMNS = u"columns"

class ExcelReader(object):
    def __init__(self, path):
        self._path = path
        name_match = re.search(r"(?P<name>[^/]+)\.xls$", path)
        self._name = name_match.groupdict()["name"]
        self._dict = None
        self._setup()
        sheet_names = self._dict.keys()

        self._lists_sheet_name = None
        for sheet_name in sheet_names:
            if sheet_name in CHOICES_SHEET_NAMES:
                self._lists_sheet_name = sheet_name

        if SURVEY_SHEET in sheet_names:
            self._fix_int_values()
            self._group_dictionaries()
            self._process_question_type()
            if self._lists_sheet_name:
                self._construct_choice_lists()
                self._insert_lists()
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
                        # this strip here is a little hacky way to clean up the data from excel, often spaces at the end of question types are breaking things
                        row_dict[key] = value.strip()
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
        choice_list = self._dict[self._lists_sheet_name]
        choices = {}
        for choice in choice_list:
            try:
                list_name = choice.pop(LIST_NAME)
            except KeyError:
                raise Exception("For some reason this choice isn't associated with a list.", choice)
            if list_name in choices: choices[list_name].append(choice)
            else: choices[list_name] = [choice]
        self._dict[self._lists_sheet_name] = choices

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
                self._prepare_multiple_choice_question(q, question_type)
            if question_type.startswith(u"begin table"):
                self._prepare_begin_table(q, question_type)

    def _prepare_multiple_choice_question(self, q, question_type):
        m = re.search(r"^(?P<select_command>select one|select all that apply) from (?P<list_name>\S+)( (?P<specify_other>or specify other))?$", question_type)
        assert m, "unsupported select syntax:" + question_type
        assert CHOICES not in q
        d = m.groupdict()
        q[CHOICES] = d["list_name"]
        if d["specify_other"]:
            q[TYPE] = " ".join([d["select_command"], d["specify_other"]])
        else:
            q[TYPE] = d["select_command"]

    def _prepare_begin_table(self, q, question_type):
        m = re.search(r"^(?P<type>begin table) with columns from (?P<list_name>\S+)$", question_type)
        assert m, "unsupported select syntax:" + question_type
        assert COLUMNS not in q
        d = m.groupdict()
        q[COLUMNS] = d["list_name"]
        q[TYPE] = d["type"]

    def _insert_lists(self):
        """
        For each multiple choice question and table in the survey find
        the corresponding list and add it to that question.
        """
        lists_by_name = self._dict[self._lists_sheet_name]
        for q in self._dict[SURVEY_SHEET]:
            self._insert_list(q, CHOICES, lists_by_name)
            self._insert_list(q, COLUMNS, lists_by_name)

    def _insert_list(self, q, key, lists_by_name):
        if key in q:
            list_name = q[key]
            if list_name not in lists_by_name:
                raise Exception("There is no list of %s by this name" % key, list_name)
            q[key] = lists_by_name[list_name]

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
                if begin_cmd[u"type"] != match_end.group(1):
                    raise Exception("This end group does not match the previous begin", cmd)
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
