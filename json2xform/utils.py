from lxml import etree
from lxml.builder import ElementMaker
import re
import codecs
import json

nsmap = {
    None : "http://www.w3.org/2002/xforms",
    "h" : "http://www.w3.org/1999/xhtml",
    "ev" : "http://www.w3.org/2001/xml-events",
    "xsd" : "http://www.w3.org/2001/XMLSchema",
    "jr" : "http://openrosa.org/javarosa",
    }

E = ElementMaker(nsmap=nsmap)

QUESTION_PREFIX = "q"
CHOICE_PREFIX = "c"
SEP = "_"

# http://www.w3.org/TR/REC-xml/
TAG_START_CHAR = r"[a-zA-Z:_]"
TAG_CHAR = r"[a-zA-Z:_0-9\-.]"
XFORM_TAG_REGEXP = "%(start)s%(char)s*" % {"start" : TAG_START_CHAR, "char" : TAG_CHAR}

def ns(abbrev, text):
    return "{" + nsmap[abbrev] + "}" + text

def is_valid_xml_tag(tag):
    return re.search(r"^" + XFORM_TAG_REGEXP + r"$", tag)

def node(*args, **kwargs):
    return E(*args, **kwargs)

def get_pyobj_from_json(str_or_path):
    """
    This function takes either a json string or a path to a json file,
    it loads the json into memory and returns the corresponding Python
    object.
    """
    try:
        # see if treating str_or_path as a path works
        fp = codecs.open(str_or_path, mode="r", encoding="utf-8")
        doc = json.load(fp, encoding="utf-8")
    except IOError:
        # if it doesn't work load the text
        doc = json.loads(str_or_path)
    return doc

# def apply(function, survey):
#     l = len(survey.children)
#     function(survey)
#     if len(survey.children) > l:
#         apply(function, survey)

# def add_one_specify(survey):
#     for i in range(len(survey.children)):
#         question = survey.children[i]
#         if question.type in ["select one", "select all that apply"]:
#             if "other" in [choice[1] for choice in question.choices] and survey.children[i+1].text!="Please specify":
#                 d = {"name" : question.name + " other",
#                      "text" : "Please specify",
#                      "type" : "string",
#                      "relevant" : "selected([%s], 'other')" % question.name}
#                 new_question = Question(**d)
#                 new_list = survey.children[0:i+1]
#                 new_list.append(new_question)
#                 new_list.extend(survey.children[i+1:len(survey.children)])
#                 survey.children = new_list
#                 return

# def main(path):
#     folder, filename = os.path.split(path)
#     m = re.search(r"([^\.]+)\.([^\.]+)$", filename)
#     filename = m.group(1).title()
#     title = m.group(1).title()
#     outfile = os.path.join("xforms", filename + ".xml")

#     survey = survey_from_text(path)
#     survey.title = title
#     apply(fake_one_table, survey)
#     apply(add_one_specify, survey)

#     f = open(outfile, "w")
#     xml_str = survey_to_xml(survey).encode("utf-8")
#     f.write(xml_str)
#     f.close()
