from itertools import chain
import json
import re
import settings
from pandas.core.frame import DataFrame
from pandas.io.parsers import ExcelWriter
from pyxform.survey import Survey
from pyxform.survey_element import SurveyElement
from pyxform.section import Section, RepeatingSection
from pyxform.question import Question
from odk_viewer.models.data_dictionary import ParsedInstance, DataDictionary
from utils.export_tools import question_types_to_exclude
from collections import OrderedDict
from common_tags import ID, XFORM_ID_STRING, STATUS, ATTACHMENTS, GEOLOCATION,\
UUID, SUBMISSION_TIME, NA_REP, BAMBOO_DATASET_ID, DELETEDAT


# this is Mongo Collection where we will store the parsed submissions
xform_instances = settings.MONGO_DB.instances

# the bind type of select multiples that we use to compare
MULTIPLE_SELECT_BIND_TYPE = u"select"
GEOPOINT_BIND_TYPE = u"geopoint"

def survey_name_and_xpath_from_dd(dd):
    for e in dd.get_survey_elements():
        if isinstance(e, Survey):
            return e.name, e.get_abbreviated_xpath()

    # should never get here
    raise Exception("DataDictionary has no Survey element")


def get_valid_sheet_name(sheet_name, existing_name_list):
    # truncate sheet_name to XLSDataFrameBuilder.SHEET_NAME_MAX_CHARS
    new_sheet_name = unique_sheet_name = \
        sheet_name[:XLSDataFrameBuilder.SHEET_NAME_MAX_CHARS]

    # make sure its unique within the list
    i = 1
    generated_name = new_sheet_name
    while generated_name in existing_name_list:
        digit_length = len(str(i))
        allowed_name_len = XLSDataFrameBuilder.SHEET_NAME_MAX_CHARS - \
            digit_length
        # make name the required len
        if len(generated_name) > allowed_name_len:
            generated_name = generated_name[:allowed_name_len]
        generated_name = "{0}{1}".format(generated_name, i)
        i += 1
    return generated_name

def remove_dups_from_list_maintain_order(l):
    return list(OrderedDict.fromkeys(l))


class NoRecordsFoundError(Exception):
    pass


class AbstractDataFrameBuilder(object):

    # TODO: use constants from comman_tags module!
    INTERNAL_FIELDS = [XFORM_ID_STRING, STATUS, ID, ATTACHMENTS, GEOLOCATION,
        UUID, SUBMISSION_TIME, BAMBOO_DATASET_ID, DELETEDAT]

    """
    Group functionality used by any DataFrameBuilder i.e. XLS, CSV and KML
    """
    def __init__(self, username, id_string, filter_query=None):
        self.username = username
        self.id_string = id_string
        self.filter_query = filter_query
        self._setup()

    def _setup(self):
        self.dd = DataDictionary.objects.get(user__username=self.username,
            id_string=self.id_string)
        self.select_multiples = self._collect_select_multiples(self.dd)
        self.gps_fields = self._collect_gps_fields(self.dd)

    @classmethod
    def _fields_to_select(cls, dd):
        return [c.get_abbreviated_xpath() for c in \
            dd.get_survey_elements() if isinstance(c, Question)]

    @classmethod
    def _collect_select_multiples(cls, dd):
        return dict([(e.get_abbreviated_xpath(), [c.get_abbreviated_xpath()\
                    for c in e.children])
            for e in dd.get_survey_elements() if e.bind.get("type")=="select"])

    @classmethod
    def _split_select_multiples(cls, record, select_multiples):
        # find any select multiple(s) columns in this record
        multi_select_columns = [key for key in record if key in
            select_multiples.keys()]
        for key, choices in select_multiples.items():
            if key in record:
                # split selected choices by spaces and join by / to the
                # element's xpath
                selections = ["%s/%s" % (key, r) for r in\
                             record[key].split(" ")]
                # remove the column since we are adding separate columns
                # for each choice
                record.pop(key)
                # add columns to record for every choice, with default
                # False and set to True for items in selections
                record.update(dict([(choice, choice in selections)\
                            for choice in
                    choices]))

            # recurs into repeats
            for record_key, record_item in record.items():
                if type(record_item) == list:
                    for list_item in record_item:
                        if type(list_item) == dict:
                            cls._split_select_multiples(list_item,
                                select_multiples)
        return record

    @classmethod
    def _collect_gps_fields(cls, dd):
        return [e.get_abbreviated_xpath() for e in dd.get_survey_elements()
            if e.bind.get("type")=="geopoint"]

    @classmethod
    def _split_gps_fields(cls, record, gps_fields):
        updated_gps_fields = {}
        for key, value in record.iteritems():
            if key in gps_fields and isinstance(value, basestring):
                gps_xpaths = DataDictionary.get_additional_geopoint_xpaths(key)
                gps_parts = dict([(xpath, None) for xpath in gps_xpaths])
                # hack, check if its a list and grab the object within that
                parts = value.split(' ')
                # TODO: check whether or not we can have a gps recording
                # from ODKCollect that has less than four components,
                # for now we are assuming that this is not the case.
                if len(parts) == 4:
                    gps_parts = dict(zip(gps_xpaths, parts))
                updated_gps_fields.update(gps_parts)
            # check for repeats within record i.e. in value
            elif type(value) == list:
                for list_item in value:
                    if type(list_item) == dict:
                        cls._split_gps_fields(list_item, gps_fields)
        record.update(updated_gps_fields)

    def _query_mongo(self, query='{}', start=0,
        limit=ParsedInstance.DEFAULT_LIMIT, fields='[]'):
        # ParsedInstance.query_mongo takes params as json strings
        # so we dumps the fields dictionary
        count_args = {
            'username': self.username,
            'id_string': self.id_string,
            'query': query,
            'fields': '[]',
            'sort': '{}',
            'count': True
        }
        count = ParsedInstance.query_mongo(**count_args)
        if count[0]["count"] == 0:
            raise NoRecordsFoundError("No records found for your query")
        query_args = {
            'username': self.username,
            'id_string': self.id_string,
            'query': query,
            'fields': fields,
            #TODO: we might want to add this in for the user 
            #to sepcify a sort order
            'sort': '{}',
            'start': start,
            'limit': limit,
            'count': False # TODO: we never count when exporting
        }
        # use ParsedInstance.query_mongo
        cursor = ParsedInstance.query_mongo(**query_args)
        return cursor


class XLSDataFrameBuilder(AbstractDataFrameBuilder):
    """
    Generate structures from mongo and DataDictionary for a DataFrameXLSWriter

    This builder can choose to query the data in batches and write to a single
    ExcelWriter object using multiple instances of DataFrameXLSWriter
    """
    INDEX_COLUMN = u"_index"
    PARENT_TABLE_NAME_COLUMN = u"_parent_table_name"
    PARENT_INDEX_COLUMN = u"_parent_index"
    EXTRA_COLUMNS = [INDEX_COLUMN, PARENT_TABLE_NAME_COLUMN,
        PARENT_INDEX_COLUMN]
    SHEET_NAME_MAX_CHARS = 30
    XLS_SHEET_COUNT_LIMIT = 255
    XLS_COLUMN_COUNT_MAX = 255

    def __init__(self, username, id_string, filter_query=None):
        super(XLSDataFrameBuilder, self).__init__(username, id_string,
            filter_query)

    def _setup(self):
        super(XLSDataFrameBuilder, self)._setup()
        # need to split columns, with repeats in individual sheets and
        # everything else on the default sheet
        self._generate_sections()

    def export_to(self, file_path):
        self.xls_writer = ExcelWriter(file_path)

        # query in batches and for each batch create an XLSDataFrameWriter and
        # write to existing xls_writer object

        # get records from mongo - do this on export so we can batch if we
        # choose to, as we should
        cursor = self._query_mongo(self.filter_query)

        data = self._format_for_dataframe(cursor)

        #TODO: batching will not work as expected since indexes are calculated
        # based the current batch, a new batch will re-calculate indexes and if
        # they are going into the same excel file, we'll have duplicates
        # possible solution - keep track of the last index from each section

        # write all cursor's data to different sheets
        # TODO: for every repeat, the index should be re-calculated
        for section in self.sections:
            # TODO: currently ignoring nested repeat data which will have no
            # records
            records = data[section["name"]]
            if len(records) > 0:
                section_name = section["name"]
                columns = section["columns"] + self.EXTRA_COLUMNS
                writer = XLSDataFrameWriter(records, columns)
                writer.write_to_excel(self.xls_writer, section_name,
                        header=True, index=False)
        self.xls_writer.save()

    def _format_for_dataframe(self, cursor):
        """
        Format each record for consumption by a dataframe

        returns a dictionary with keys being the names of the sheet and values
        a list of dicts to feed into a DataFrame
        """
        data = {}
        for section_name in self.section_names_list:
            data[section_name] = []

        for record in cursor:
            # from record, we'll end up with multiple records, one for each
            # section we have

            # add records for the default section
            columns = self._get_section(self.survey_name)["columns"]
            index = self._add_data_for_section(data[self.survey_name],
                record, columns)

            for sheet_name in self.section_names_list:
                section = self._get_section(sheet_name)
                # skip default section i.e surveyname
                if sheet_name != self.survey_name:
                    xpath = section["xpath"]
                    columns = section["columns"]
                    # TODO: handle nested repeats -ignoring nested repeats for
                    # now which will not be in the top level record, perhaps
                    # nest sections as well so we can recurs in and get them
                    if record.has_key(xpath):
                        repeat_records = record[xpath]
                        for repeat_record in repeat_records:
                            self._add_data_for_section(data[sheet_name],
                                repeat_record, columns, index,\
                                self.survey_name)

        return data

    def _add_data_for_section(self, data_section, record, columns,
                parent_index = -1, parent_table_name = None):
        data_section.append({})
        index = len(data_section)
        #data_section[len(data_section)-1].update(record) # we could simply do
        # this but end up with duplicate data from repeats

        # find any select multiple(s) and add additional columns to record
        record = self._split_select_multiples(record, self.select_multiples)
        # alt, precision
        self._split_gps_fields(record, self.gps_fields)
        for column in columns:
            try:
                data_section[len(data_section)-1].update({column:
                    record[column]})
            except KeyError:
                # a record may not have responses for some elements simply
                # because they were not captured
                pass

        data_section[len(data_section)-1].update({
            XLSDataFrameBuilder.INDEX_COLUMN: index,
            XLSDataFrameBuilder.PARENT_INDEX_COLUMN: parent_index,
            XLSDataFrameBuilder.PARENT_TABLE_NAME_COLUMN: parent_table_name})
        return index

    def _generate_sections(self):
        """
        Split survey questions into separate sections for each xls sheet and
        columns for each section
        """
        # clear list
        self.sections = []

        # dict of section name to their indexes within self.sections
        self.section_names_list = {}

        # TODO: make sure survey name and any section name is a valid xml
        # sheet name i.e. 31 chars or less etc.
        self.survey_name, survey_xpath = survey_name_and_xpath_from_dd(self.dd)

        # generate a unique and valid xls sheet name
        self.survey_name = get_valid_sheet_name(self.survey_name,
                self.sections)
        # setup the default section
        self._create_section(self.survey_name, survey_xpath, False)

        # dict of select multiple elements
        self.select_multiples = {}

        # get form elements to split repeats into separate section/sheets and
        # everything else in the default section
        for e in self.dd.get_survey_elements():
            # check for a Section or sub-classes of
            if isinstance(e, Section):
                # always default to the main sheet
                sheet_name = self.survey_name

                # if a repeat we use its name
                if isinstance(e, RepeatingSection):
                    sheet_name = e.name
                    sheet_name = get_valid_sheet_name(sheet_name,
                            self.sections)
                    self._create_section(sheet_name, e.get_abbreviated_xpath(),
                            True)

                # for each child add to survey_sections
                for c in e.children:
                    if isinstance(c, Question) and not \
                            question_types_to_exclude(c.type)\
                    and not c.bind.get(u"type") == MULTIPLE_SELECT_BIND_TYPE:
                            self._add_column_to_section(sheet_name, c)
                    elif c.bind.get(u"type") == MULTIPLE_SELECT_BIND_TYPE:
                        self.select_multiples[c.get_abbreviated_xpath()] = \
                        [option.get_abbreviated_xpath() for option in
                                c.children]
                        # if select multiple, get its choices and make them
                        # columns
                        for option in c.children:
                            self._add_column_to_section(sheet_name, option)
                    # split gps fields within this section
                    if c.bind.get(u"type") == GEOPOINT_BIND_TYPE:
                        # add columns for geopint components
                        for xpath in\
                            self.dd.get_additional_geopoint_xpaths(
                            c.get_abbreviated_xpath()):
                            self._add_column_to_section(sheet_name, xpath)
        self.get_exceeds_xls_limits()

    def get_exceeds_xls_limits(self):
        if not hasattr(self, "exceeds_xls_limits"):
            self.exceeds_xls_limits = False
            if len(self.sections) > self.XLS_SHEET_COUNT_LIMIT:
                self.exceeds_xls_limits = True
            else:
                for section in self.sections:
                    if len(section["columns"]) > self.XLS_COLUMN_COUNT_MAX:
                        self.exceeds_xls_limits = True
                        break
        return self.exceeds_xls_limits

    def _create_section(self, section_name, xpath, is_repeat):
        index = len(self.sections)
        self.sections.append({"name": section_name, "xpath": xpath,
                              "columns": [], "is_repeat": is_repeat})
        self.section_names_list[section_name] = index

    def _add_column_to_section(self, sheet_name, column):
        section = self._get_section(sheet_name)
        xpath = None
        if isinstance(column, SurveyElement):
            xpath = column.get_abbreviated_xpath()
        elif isinstance(column, basestring):
            xpath = column
        assert(xpath)
        # make sure column is not already in list
        if xpath not in section["columns"]:
            section["columns"].append(xpath)

    def _get_section(self, section_name):
        return self.sections[self.section_names_list[section_name]]


class CSVDataFrameBuilder(AbstractDataFrameBuilder):

    def __init__(self, username, id_string, filter_query=None):
        super(CSVDataFrameBuilder, self).__init__(username,
            id_string, filter_query)
        self.ordered_columns = OrderedDict()

    def _setup(self):
        super(CSVDataFrameBuilder, self)._setup()

    @classmethod
    def _reindex(cls, key, value, ordered_columns, parent_prefix = None):
        """
        Flatten list columns by appending an index, otherwise return as is
        """
        d = {}

        # check for lists
        if type(value) is list and len(value) > 0:
            for index, item in enumerate(value):
                # start at 1
                index += 1
                # for each list check for dict, we want to transform the key of
                # this dict
                if type(item) is dict:
                    for nested_key, nested_val in item.iteritems():
                        xpaths = nested_key.split('/')
                        # second level so we must have at least 2 elements
                        assert(len(xpaths) > 1)
                        # append index to the second last column i.e. group
                        # name
                        xpaths[-2] += "[%d]" % index
                        new_prefix = xpaths[:-1]
                        if type(nested_val) is list:
                            # if nested_value is a list, rinse and repeat
                            d.update(cls._reindex(nested_key, nested_val,
                                ordered_columns, new_prefix))
                        else:
                            # it can only be a scalar
                            # collapse xpath
                            if parent_prefix:
                                xpaths[0:len(parent_prefix)] = parent_prefix
                            new_xpath = u"/".join(xpaths)
                            # check if this key exists in our ordered columns
                            if key in ordered_columns.keys():
                                if not new_xpath in ordered_columns[key]:
                                    ordered_columns[key].append(new_xpath)
                            d[new_xpath] = nested_val
                else:
                    d[key] = value
        else:
            # anything that's not a list will be in the top level dict so its
            # safe to simply assign
            d[key] = value
        return d

    @classmethod
    def _build_ordered_columns(cls, survey_element, ordered_columns,
            is_repeating_section=False):
        """
        Build a flat ordered dict of column groups

        is_repeating_section ensures that child questions of repeating sections
        are not considered as columns
        """
        for child in survey_element.children:
            child_xpath = child.get_abbreviated_xpath()
            if isinstance(child, Section):
                child_is_repeating = False
                if isinstance(child, RepeatingSection):
                    ordered_columns[child.get_abbreviated_xpath()] = []
                    child_is_repeating = True
                cls._build_ordered_columns(child, ordered_columns,
                    child_is_repeating)
            elif isinstance(child, Question) and not \
                question_types_to_exclude(child.type) and not\
                    is_repeating_section:# if is_repeating_section, its parent
                    # already initiliased an empty list so we dont add it to our
                    # list of columns, the repeating columns list will be
                    # generated when we reindex
                ordered_columns[child.get_abbreviated_xpath()] = None

    def _format_for_dataframe(self, cursor):
        # TODO: check for and handle empty results
        self.ordered_columns = OrderedDict()
        self._build_ordered_columns(self.dd.survey, self.ordered_columns)
        # add ordered columns for select multiples
        for key, choices in self.select_multiples.items():
            # HACK to ensure choices are NOT duplicated
            self.ordered_columns[key] = remove_dups_from_list_maintain_order(
                choices)
        # add ordered columns for gps fields
        for key in self.gps_fields:
            gps_xpaths = self.dd.get_additional_geopoint_xpaths(key)
            self.ordered_columns[key] = [key] + gps_xpaths
        data = []
        for record in cursor:
            # split select multiples
            record = self._split_select_multiples(record,
                self.select_multiples)
            # check for gps and split into components i.e. latitude, longitude,
            # altitude, precision
            self._split_gps_fields(record, self.gps_fields)
            flat_dict = {}
            # re index repeats
            for key, value in record.iteritems():
                reindexed = self._reindex(key, value, self.ordered_columns)
                flat_dict.update(reindexed)

            data.append(flat_dict)
        return data

    def export_to(self, file_object):
        # build the query, ideally set the start and limit params for batching
        cursor = self._query_mongo(self.filter_query)
        # generate list of select multiples to be used in format_for_dataframe
        data = self._format_for_dataframe(cursor)
        columns = list(chain.from_iterable([[xpath] if cols == None else cols\
                    for xpath, cols in self.ordered_columns.iteritems()]))
        writer = CSVDataFrameWriter(data, columns)
        writer.write_to_csv(file_object)

class XLSDataFrameWriter(object):
    def __init__(self, records, columns):
        self.dataframe = DataFrame(records, columns=columns)

    def write_to_excel(self, excel_writer, sheet_name, header=False,
        index=False):
        self.dataframe.to_excel(excel_writer, sheet_name, header=header,
                index=index)

class CSVDataFrameWriter(object):
    def __init__(self, records, columns):
        # TODO: if records is empty, raise a known exception
        # catch it in the view and handle
        assert(len(records) > 0)
        self.dataframe = DataFrame(records, columns=columns)

        # remove columns we don't want
        for col in AbstractDataFrameBuilder.INTERNAL_FIELDS:
            if col in self.dataframe.columns:
                del(self.dataframe[col])

    def write_to_csv(self, csv_file, index=False):
        self.dataframe.to_csv(csv_file, index=index, na_rep=NA_REP,
                              encoding='utf-8')
