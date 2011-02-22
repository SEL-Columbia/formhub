import sys
from xls2json import ExcelReader
from builder import create_survey_element_from_json

def xls2json(name):
    converter = ExcelReader("%s.xls" % name)
    converter.print_json_to_file()

def json2xform(name):
    s = create_survey_element_from_json("%s.json" % name)
    s.print_xform_to_file()

def xls2xform(name):
    xls2json(name)
    json2xform(name)

if __name__=="__main__":
    name = sys.argv[1]
    xls2xform(name)
