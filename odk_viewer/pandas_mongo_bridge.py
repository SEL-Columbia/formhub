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

def survey_name_and_xpath_from_dd(dd):
    for e in dd.get_survey_elements():
        if isinstance(e, Survey):
            return e.name, e.get_abbreviated_xpath()

    # should never get here
    raise Exception("DataDictionary has no Survey element")

def get_valid_sheet_name(sheet_name, existing_name_list):
    # truncate sheet_name to XLSDataFrameBuilder.SHEET_NAME_MAX_CHARS
    new_sheet_name = unique_sheet_name = sheet_name[:XLSDataFrameBuilder.SHEET_NAME_MAX_CHARS]

    # make sure its unique within the list
    i = 1
    generated_name = new_sheet_name
    while generated_name in existing_name_list:
        digit_length = len(str(i))
        allowed_name_len = XLSDataFrameBuilder.SHEET_NAME_MAX_CHARS - digit_length
        # make name the required len
        if len(generated_name) > allowed_name_len:
            generated_name = generated_name[:allowed_name_len]
        generated_name = "{0}{1}".format(generated_name, i)
        i += 1
    return generated_name

class AbstractDataFrameBuilder:
    """
    Used to group functionality used by any DataFrameBuilder i.e. XLS, CSV and KML
    """
    def __init__(self, username, id_string):
        self.set_up(username, id_string)

    def _query_mongo(self, filter_query = None):
        query = {ParsedInstance.USERFORM_ID: u'%s_%s' % (self.username, self.id_string)}
        cursor = xform_instances.find(query)
        return cursor

    def set_up(self, username, id_string):
        self.username = username
        self.id_string = id_string

class XLSDataFrameBuilder(AbstractDataFrameBuilder):
    """
    Builds required structures from mongo and DataDictionary for a DataFrameXLSWriter

    This builder can choose to query the data in batches and write to a single ExcelWriter object using multiple
    instances of DataFrameXLSWriter
    """
    EXTRA_COLUMNS = ["_index", "_parent_table_name", "_parent_index"]
    SHEET_NAME_MAX_CHARS = 30

    def __init__(self, username, id_string):
        AbstractDataFrameBuilder.__init__(self, username, id_string)

    def set_up(self, username, id_string):
        AbstractDataFrameBuilder.set_up(self, username, id_string)
        # need to split columns, with repeats in individual sheets and everything else on the default sheet
        self._generate_sections()

    def export_to(self, file_path):
        self.xls_writer = ExcelWriter(file_path)

        # query in batches and for each batch create an XLSDataFrameWriter and write to existing xls_writer object

        # get records from mongo - do this on export so we can batch if we choose to, as we should
        cursor = self._query_mongo() #TODO: query using ParsedInstance.query_mongo

        data = self._format_for_dataframe(cursor)

        #TODO: batching will not work as expected since indexes are calculated based the current batch, a new batch ..
        #TODO: .. will re-calculate indexes and if they are going into the same excel file, we'll have duplicates
        #TODO: .. possible solution - keep track of the last index from each section

        # write all cursor's data to different sheets
        for section in self.sections:
            # TODO: currently ignoring nested repeat data which will have no records
            records = data[section["name"]]
            if len(records) > 0:
                section_name = section["name"]
                columns = section["columns"] + self.EXTRA_COLUMNS
                writer = XLSDataFrameWriter(records, columns)
                writer.write_to_excel(self.xls_writer, section_name, header=True, index=False)
                self.xls_writer.save()

    def _format_for_dataframe(self, cursor):
        """
        Format each record by striping out repeats into individual records and adding indexes

        returns a dictionary with keys being the names of the sheet and values a list of dicts to feed into a DataFrame
        """
        data = {}
        for section_name in self.section_names_list:
            data[section_name] = []

        for record in cursor:
            # from record, we'll end up with multiple records, one for each section we have

            # add records for the default section
            columns = self._get_section(self.survey_name)["columns"]
            index = self._add_data_for_section(data[self.survey_name], record, columns)

            for sheet_name in self.section_names_list:
                section = self._get_section(sheet_name)
                # skip default section i.e surveyname
                if sheet_name != self.survey_name:
                    xpath = section["xpath"]
                    columns = section["columns"]
                    # TODO: handle nested repeats -ignoring nested repeats for now which will not be in the top level..
                    # TODO: ..record, perhaps nest sections as well so we can recurs in and get them
                    if record.has_key(xpath):
                        repeat_records = record[xpath]
                        for repeat_record in repeat_records:
                            self._add_data_for_section(data[sheet_name], repeat_record, columns, index)

        return data

    def _add_data_for_section(self, data_section, record, columns, parent_index = -1):
        data_section.append({})
        index = len(data_section)
        #data_section[len(data_section)-1].update(record) # we could simply do this but end up with duplicate data from repeats

        # find any select multiple(s) and add additional columns to record
        multi_select_keys = [key for key in record if key in self.select_multiples.keys()]
        for key in multi_select_keys:
            choices = self.select_multiples[key]

            # split selected choices by spaces and join by / to the element's xpath
            selections = ["%s/%s" % (key, r) for r in record[key].split(" ")]

            # add columns to record for every choice, with default False and set to True for items in selections
            record.update(dict([(choice, choice in selections) for choice in choices]))

            # remove the column since we are adding separate columns for each choice
            record.pop(key)
        for column in columns:
            try:
                data_section[len(data_section)-1].update({column: record[column]})
            except KeyError:
                #TODO: none of the columns should be missing after we fix select multiples
                print "Missing column %s\n" % column
                pass
        data_section[len(data_section)-1].update({"_index": index, "_parent_index": parent_index})
        return index

    def _generate_sections(self):
        """
        Split survey questions into separate sections for each xls sheet and columns for each section
        """
        # clear list
        self.sections = []

        # dict of section name to their indexes within self.sections
        self.section_names_list = {}

        dd = DataDictionary.objects.get(user__username=self.username, id_string=self.id_string)

        # TODO: make sure survey name and any section name is a valid xml sheet name i.e. 31 chars or less etc.
        self.survey_name, survey_xpath = survey_name_and_xpath_from_dd(dd) # also the default sheet name is excel

        # setup the default section
        self._create_section(self.survey_name, survey_xpath, False)

        # dict of select multiple elements
        self.select_multiples = {}

        # get form elements to split repeats into separate section/sheets and everything else in the default section
        for e in dd.get_survey_elements():
            # check for a Section or sub-classes of
            if isinstance(e, Section):
                # always default to the main sheet
                sheet_name = self.survey_name

                # if a repeat we use its name
                if isinstance(e, RepeatingSection):
                    sheet_name = e.name
                    self._create_section(sheet_name, e.get_abbreviated_xpath(), True)

                # for each child add to survey_sections
                for c in e.children:
                    if isinstance(c, Question) and not question_types_to_exclude(c.type)\
                    and not c.bind.get(u"type") == MULTIPLE_SELECT_BIND_TYPE:
                        self._add_column_to_section(sheet_name, c)
                    elif c.bind.get(u"type") == MULTIPLE_SELECT_BIND_TYPE:
                        self.select_multiples[c.get_abbreviated_xpath()] = \
                        [option.get_abbreviated_xpath() for option in c.children]
                        # if select multiple, get its choices and make them columns
                        for option in c.children:
                            self._add_column_to_section(sheet_name, option)

    def _create_section(self, section_name, xpath, is_repeat):
        index = len(self.sections)
        self.sections.append({"name": section_name, "xpath": xpath, "columns": [], "is_repeat": is_repeat})
        self.section_names_list[section_name] = index

    def _add_column_to_section(self, sheet_name, column):
        self._get_section(sheet_name)["columns"].append(column.get_abbreviated_xpath())

    def _get_section(self, section_name):
        return self.sections[self.section_names_list[section_name]]

class XLSDataFrameWriter:
    def __init__(self, records, columns):
        self.dataframe = DataFrame(records, columns=columns)

    def write_to_excel(self, excel_writer, sheet_name, header=False, index=False):
        self.dataframe.to_excel(excel_writer, sheet_name, header=header, index=index)