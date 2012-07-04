import settings, re, copy
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

def remove_indexes_from_xpath(xpath):
    return re.sub(r"\[\d+\]", "", xpath)

def get_groupname_from_xpath(xpath):
    # remove indexes form xpath
    clean_xpath = remove_indexes_from_xpath(xpath)

    # match upto last /something
    match = re.match(r"(.+)?/(\w.+)?", clean_xpath)
    if match:
        return match.groups()[0]
    else:
        return None

def survey_name_and_xpath_from_dd(dd):
    for e in dd.get_survey_elements():
        if isinstance(e, Survey):
            return e.name, e.get_abbreviated_xpath()

    # should never get here
    raise Exception

def pos_and_parent_pos_from_repeat(repeat):
    """
    From an indexed repeat i.e. parent[2]/child/item get the position of its parent and its own position within a record
    We don't use index since index its position in the entire set of records
    """
    parent_pos = 1
    pos = 1
    # check for a trailing ]
    end = repeat.rfind("]")
    # find the matching [
    start = repeat.rfind("[")
    if end > -1 and start > -1:
        pass
    return pos, parent_pos

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
    EXTRA_COLUMNS = ["_index", "_parent_table_name", "_parent_index"]

    def __init__(self, username, id_string):
        AbstractDataFrameBuilder.__init__(self, username, id_string)

    def setUp(self, username, id_string):
        AbstractDataFrameBuilder.setUp(self, username, id_string)
        # need to split columns, with repeats in individual sheets and everything else on the default sheet
        self._generateSections()

    def exportTo(self, file_path):
        self.xls_writer = ExcelWriter(file_path)

        # query in batches and for each batch create an XLSDataFrameWriter and write to existing xls_writer object

        # get records from mongo - do this on export so we can batch if we choose to, as we should
        cursor = self._queryMongo() #TODO: query using ParsedInstance.query_mongo

        data = self._formatForDataframe(cursor)
        print "data: %s" % data

        #TODO: batching will not work as expected since indexes are calculated based the current batch, a new batch ..
        #TODO: .. will re-calculate indexes and if they are going into the same excel file, we'll have duplicates
        #TODO: .. possible solution - keep track of the lats index from each section
        # write all cursor's data to different sheets
        for section_name, records in data.iteritems():
            section = self.sections[section_name]
            columns = section["columns"]
            writer = XLSDataFrameWriter(records, columns)
            writer.writeToExcel(self.xls_writer, section_name, header=True, index=False)
            self.xls_writer.save()

    def _formatForDataframe(self, cursor):
        """
        Do any housekeeping on mongo data to get it ready for a Pandas Dataframe

        Assign each repeat as an additional dict for its particular section
        1. Remove indexes from repeat column names i.e. parent[2]/child to parent/child
        2. Split a select-multiple into its components
        3. Associate any repeats with its parent by including parent_index and parent_table fields

        returns a dictionary with keys being the names of the sheet and values a list of dicts to feed into a DataFrame
        """
        data = {}
        records_tpl = {} # blank template for initialising records
        for section_name in self.sections:
            #HACK append extra columns here
            self.sections[section_name]["columns"] += self.EXTRA_COLUMNS
            data[section_name] = [{}]

        records_tpl = copy.copy(data)

        for record in cursor:
            # from record, we'll end up with multiple records, one for each section we have
            records = copy.copy(records_tpl)

            # setup _index for the default section - NOT zero based
            index = len(data[self.survey_name])
            data[self.survey_name].update({"_index": len(data[self.survey_name])})
            for key, val in record.iteritems():
                current_section_name = None

                # remove indexes so we can match existing xpaths/columns
                clean_xpath = remove_indexes_from_xpath(key)

                # check in the columns for each of our sections to find a match
                for section_name, xpath_and_columns in self.sections.iteritems():
                    columns = xpath_and_columns["columns"]
                    if clean_xpath in columns:
                        current_section_name = section_name
                        break

                # we only consider items assigned to a section name for export,
                if current_section_name:
                    section = self.sections[current_section_name]
                    is_repeat = section["is_repeat"]

                    #data[current_section_name][len(data[current_section_name])-1].update({key: val})
                    #index = len(records[current_section_name])-1

            #TODO: figure how to append data from within previous loop to eliminate additional loop
            #for section_name, r in records.iteritems():
            #    data[section_name].append(r)

        return data

    def _generateSections(self):
        """
        Split survey questions into separate sections for each xls sheet and columns for each section
        """
        # clear list
        self.sections = {}

        dd = DataDictionary.objects.get(user__username=self.username, id_string=self.id_string)
        self.survey_name, survey_xpath = survey_name_and_xpath_from_dd(dd) # also the default sheet name is excel

        # setup the default section
        self.sections[self.survey_name] = {"xpath": survey_xpath, "columns": [], "is_repeat": False}

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
                    self.sections[sheet_name] = {"xpath": e.get_abbreviated_xpath(), "columns": [],"is_repeat": True}
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

    def writeToExcel(self, excel_writer, sheet_name, header=False, index=False):
        self.dataframe.to_excel(excel_writer, sheet_name, header=header, index=index)