"""
A Python script to convert excel files into JSON.
"""

from xlrd import open_workbook
import json
import sys

SURVEY = u"survey"
CHOICES = u"choices"
CHOICE_LIST_NAME = u"list name"
TEXT = u"text"
TEXT_PREFACE = TEXT + u":"
TYPE = u"type"
RESERVED_FIELDS = [u"name", u"text", u"hint", u"type", u"choices", u"attributes"]
ATTRIBUTES = u"attributes"

class ExcelToJsonConverter(object):
    def __init__(self, path):
        self._path = path
        self._pyobj = None

        self._step1()
        self._clean_text()
        self._clean_choice_lists()
        self._fix_int_values()
        self._insert_choice_lists()
        self._group_extra_attributes()

    def to_dict(self):
        return self._pyobj

    def get_json(self):
        return json.dumps(self._pyobj, indent=4)

    def _step1(self):
        """
        Return
        {
        "sheet1.name" : [
        {col1.header : value[2,1], col2.header : value[2,2]}, ...
        ]
        "sheet2.name" : [ ...
        ]
        }
        """
        workbook = open_workbook(self._path)
        self._pyobj = {}
        for sheet in workbook.sheets():
            self._pyobj[sheet.name] = []
            for row in range(1,sheet.nrows):
                row_dict = {}
                for column in range(0,sheet.ncols):
                    key = sheet.cell(0,column).value
                    value = sheet.cell(row,column).value
                    if value:
                        row_dict[key] = value
                if row_dict: self._pyobj[sheet.name].append(row_dict)

    def _clean_text(self):
        for dicts in self._pyobj.values():
            for d in dicts:
                text = {}
                for k, v in d.items():
                    if k.startswith(TEXT_PREFACE):
                        text[k[len(TEXT_PREFACE):]] = v
                        del d[k]
                assert TEXT not in d
                if text: d[TEXT] = text

    def _clean_choice_lists(self):
        choice_list = self._pyobj[CHOICES]
        choices = {}
        for choice in choice_list:
            list_name = choice.pop(CHOICE_LIST_NAME)
            if list_name in choices: choices[list_name].append(choice)
            else: choices[list_name] = [choice]
        self._pyobj[CHOICES] = choices

    def _fix_int_values(self):
        for choice_list in self._pyobj[CHOICES].values():
            for choice in choice_list:
                v = choice[u"value"]
                if type(v)==float and v==int(v):
                    choice[u"value"] = int(v)

    def _insert_choice_lists(self):
        survey = self._pyobj[SURVEY]
        for i in range(len(survey)):
            if survey[i][TYPE].startswith(u"select"):
                q_type, list_name = survey[i][TYPE].split(u"from")
                survey[i][TYPE] = q_type.strip()
                assert u"choices" not in survey[i]
                survey[i][u"choices"] = self._pyobj[CHOICES][list_name.strip()]
        self._pyobj = survey

    def _group_extra_attributes(self):
        for q in self._pyobj:
            assert ATTRIBUTES not in q
            q[ATTRIBUTES] = {}
            for k in q.keys():
                if k not in RESERVED_FIELDS:
                    q[ATTRIBUTES][k] = q[k]
                    del q[k]

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
