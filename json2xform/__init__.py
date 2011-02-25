import sys

from survey import Survey
from question import MultipleChoiceQuestion, InputQuestion
from xls2json import ExcelReader
from instance import SurveyInstance

if __name__=="__main__":
    path = sys.argv[1]
    assert path[-4:]==".xls"
    converter = ExcelReader(path)
    converter.print_json_to_file()
    s = Survey(name=path[:-4])
    s.load_elements_from_json(path[:-4]+".json")
    print s.to_xml()
