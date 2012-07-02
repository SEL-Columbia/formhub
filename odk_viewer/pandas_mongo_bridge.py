import settings
from pandas.core.frame import DataFrame
from pandas.io.parsers import ExcelWriter
from pyxform.survey import Survey
from pyxform.section import Section,RepeatingSection
from pyxform.question import Question
from odk_viewer.models.data_dictionary import ParsedInstance, DataDictionary
from utils.export_tools import question_types_to_exclude

# this is Mongo Collection where we will store the parsed submissions
xform_instances = settings.MONGO_DB.instances

# the bind type of select multiples that we use to compare
MULTIPLE_SELECT_BIND_TYPE = u"select"

def survey_name_and_xpath_from_dd(dd):
    for e in dd.get_survey_elements():
        if isinstance(e, Survey):
            return e.name, e.get_abbreviated_xpath()

    # should never get here
    raise Exception

class AbstractDataFrameBuilder:
    """
    Used to group functionality used by any DataFrameBuilder i.e. XLS, CSV and KML
    """
    def __init__(self, username, id_string):
        self.setUp(username, id_string)

    def _queryMongo(self, filter_query = None):
        query = {ParsedInstance.USERFORM_ID: u'%s_%s' % (self.username, self.id_string)}
        cursor = xform_instances.find(query)
        return cursor

    def setUp(self, username, id_string):
        self.username = username
        self.id_string = id_string

class XLSDataFrameBuilder(AbstractDataFrameBuilder):
    """
    Builds required structures from mongo and DataDictionary for a DataFrameXLSWriter

    This builder can choose to query the data in batches and write to a single ExcelWriter object using multiple
    instances of DataFrameXLSWriter
    """

    def __init__(self, username, id_string):
        AbstractDataFrameBuilder.__init__(self, username, id_string)

    def setUp(self, username, id_string):
        AbstractDataFrameBuilder.setUp(self, username, id_string)
        # need to split columns, with repeats in individual sheets and everything else on the default sheet
        self._generateSections()

    def exportTo(self, file_path):
        self.xls_writer = ExcelWriter(file_path)

        # get records from mongo - do this on export so we can batch if we choose to, as we should
        cursor = self._queryMongo()

    def _generateSections(self):
        # clear list
        self.sections = {}

        dd = DataDictionary.objects.get(user__username=self.username, id_string=self.id_string)
        self.survey_name, survey_xpath = survey_name_and_xpath_from_dd(dd) # also the default sheet name is excel

        # setup the default section
        self.sections[self.survey_name] = {"xpath": survey_xpath, "columns": []}

        #TODO: check for 'MultipleChoiceQuestion's and collect its 'pyxform.question.Option's as columns, but to which sheet
        self.multi_selects = {}

        # get form elements to split repeats into separate sheets and everything else in the main sheet
        for e in dd.get_survey_elements():
            # check for a Section or sub-classes of
            if isinstance(e, Section):
                # always default to the main sheet
                sheet_name = self.survey_name

                # if a repeat we use its name
                if isinstance(e, RepeatingSection):
                    sheet_name = e.name
                    self.sections[sheet_name] = {"xpath": e.get_abbreviated_xpath(), "columns": []}
                    #self.sheet_names_list.append(sheet_name)

                # for each child add to survey_sections
                for c in e.children:
                    if isinstance(c, Question) and not question_types_to_exclude(c.type)\
                    and not c.bind.get(u"type") == MULTIPLE_SELECT_BIND_TYPE:
                        self._addColumnToSection(sheet_name, c)
                    elif c.bind.get(u"type") == MULTIPLE_SELECT_BIND_TYPE:
                        # if select multiple, get its choices and make them columns
                        for option in c.children:
                            self._addColumnToSection(sheet_name, option)

    def _addColumnToSection(self, sheet_name, column):
        self.sections[sheet_name]["columns"].append(column.get_abbreviated_xpath())

class XLSDataFrameWriter:
    def __init__(self, records, columns):
        self.dataframe = DataFrame(records, columns=columns)

    def write_to_excel(self, excel_writer, sheet_name, header=False, index=False):
        self.dataframe.to_excel(excel_writer, sheet_name, header=header, index=index)