from survey import Survey
from question import MultipleChoiceQuestion, InputQuestion

def survey_from_json(path):
    f = open(path)
    questions = json.load(f)
    f.close()
    return Survey(title="Agriculture", questions=[q(d) for d in questions])

if __name__ == '__main__':
    s = survey_from_json(sys.argv[1])
    print s.__unicode__()
