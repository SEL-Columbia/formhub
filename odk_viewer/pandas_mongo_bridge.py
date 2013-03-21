from itertools import chain
import time
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

# column group delimiters
GROUP_DELIMITER_SLASH = '/'
GROUP_DELIMITER_DOT   = '.'
DEFAULT_GROUP_DELIMITER = GROUP_DELIMITER_SLASH
GROUP_DELIMITERS = [GROUP_DELIMITER_SLASH, GROUP_DELIMITER_DOT]


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


def get_prefix_from_xpath(xpath):
    xpath = str(xpath)
    parts = xpath.rsplit('/', 1)
    if len(parts) == 1:
        return None
    elif len(parts) == 2:
        return '%s/' % parts[0]
    else:
        raise ValueError('%s cannot be prefixed, it returns %s' % (xpath, str(parts)))


class NoRecordsFoundError(Exception):
    pass


class AbstractDataFrameBuilder(object):
    IGNORED_COLUMNS = [XFORM_ID_STRING, STATUS, ID, ATTACHMENTS, GEOLOCATION,
                       BAMBOO_DATASET_ID, DELETEDAT]
    # fields NOT within the form def that we want to include
    ADDITIONAL_COLUMNS = [UUID, SUBMISSION_TIME]

    """
    Group functionality used by any DataFrameBuilder i.e. XLS, CSV and KML
    """
    def __init__(self, username, id_string, filter_query=None,
        group_delimiter=DEFAULT_GROUP_DELIMITER, split_select_multiples=True):
        self.username = username
        self.id_string = id_string
        self.filter_query = filter_query
        self.group_delimiter = group_delimiter
        self.split_select_multiples = split_select_multiples
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
        """ Prefix contains the xpath and slash if we are within a repeat so that we can figure out which select multiples belong to which repeat
        """
        for key, choices in select_multiples.items():
            # the select multiple might be blank or not exist in the record, need to make those False
            selections = []
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
                            for choice in choices]))

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
        limit=ParsedInstance.DEFAULT_LIMIT, fields='[]', count=False):
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
        count_object = ParsedInstance.query_mongo(**count_args)
        record_count = count_object[0]["count"]
        if record_count == 0:
            raise NoRecordsFoundError("No records found for your query")
        # if count was requested, return the count
        if count:
            return record_count
        else:
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
                'count': False
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
    CURRENT_INDEX_META = 'current_index'

    def __init__(self, username, id_string, filter_query=None,
                 group_delimiter=DEFAULT_GROUP_DELIMITER,
                 split_select_multiples=True):
        super(XLSDataFrameBuilder, self).__init__(username, id_string,
            filter_query, group_delimiter, split_select_multiples)

    def _setup(self):
        super(XLSDataFrameBuilder, self)._setup()
        # need to split columns, with repeats in individual sheets and
        # everything else on the default sheet
        self._generate_sections()

    def export_to(self, file_path, batchsize=1000):
        self.xls_writer = ExcelWriter(file_path)

        # get record count
        record_count = self._query_mongo(count=True)

        # query in batches and for each batch create an XLSDataFrameWriter and
        # write to existing xls_writer object
        start = 0
        header = True
        while start < record_count:
            cursor = self._query_mongo(self.filter_query, start=start,
                limit=batchsize)

            data = self._format_for_dataframe(cursor)

            # write all cursor's data to their respective sheets
            for section_name, section in self.sections.iteritems():
                records = data[section_name]
                # TODO: currently ignoring nested repeats so ignore sections that have 0 records
                if len(records) > 0:
                    # use a different group delimiter if needed
                    columns = section["columns"]
                    if self.group_delimiter != DEFAULT_GROUP_DELIMITER:
                        columns = [self.group_delimiter.join(col.split("/")) for col in columns ]
                    columns = columns + self.EXTRA_COLUMNS
                    writer = XLSDataFrameWriter(records, columns)
                    writer.write_to_excel(self.xls_writer, section_name,
                            header=header, index=False)
            header = False
            # increment counter(s)
            start += batchsize
            time.sleep(0.1)
        self.xls_writer.save()

    def _format_for_dataframe(self, cursor):
        """
        Format each record for consumption by a dataframe

        returns a dictionary with the key being the name of the sheet, and values
        a list of dicts to feed into a DataFrame
        """
        data = dict((section_name, []) for section_name in self.sections.keys())

        main_section = self.sections[self.survey_name]
        main_sections_columns = main_section["columns"]

        for record in cursor:
            # from record, we'll end up with multiple records, one for each
            # section we have

            # add records for the default section
            self._add_data_for_section(data[self.survey_name],
                record, main_sections_columns, self.survey_name)
            parent_index = main_section[self.CURRENT_INDEX_META]

            for sheet_name, section in self.sections.iteritems():
                # skip default section i.e survey name
                if sheet_name != self.survey_name:
                    xpath = section["xpath"]
                    columns = section["columns"]
                    # TODO: handle nested repeats -ignoring nested repeats for
                    # now which will not be in the top level record, perhaps
                    # nest sections as well so we can recurs in and get them
                    if record.has_key(xpath):
                        repeat_records = record[xpath]
                        num_repeat_records = len(repeat_records)
                        for repeat_record in repeat_records:
                            self._add_data_for_section(data[sheet_name],
                                repeat_record, columns, sheet_name,
                                parent_index, self.survey_name)

        return data

    def _add_data_for_section(self, data_section, record, columns, section_name,
                parent_index = -1, parent_table_name = None):
        data_section.append({})
        self.sections[section_name][self.CURRENT_INDEX_META] += 1
        index = self.sections[section_name][self.CURRENT_INDEX_META]
        #data_section[len(data_section)-1].update(record) # we could simply do
        # this but end up with duplicate data from repeats

        if self.split_select_multiples:
            # find any select multiple(s) and add additional columns to record
            record = self._split_select_multiples(record, self.select_multiples)
        # alt, precision
        self._split_gps_fields(record, self.gps_fields)
        for column in columns:
            data_value = None
            try:
                data_value = record[column]
            except KeyError:
                # a record may not have responses for some elements simply
                # because they were not captured
                pass
            data_section[
                len(data_section)-1].update({self.group_delimiter.join(column.split('/')) if self.group_delimiter != DEFAULT_GROUP_DELIMITER else column: data_value})

        data_section[len(data_section)-1].update({
            XLSDataFrameBuilder.INDEX_COLUMN: index,
            XLSDataFrameBuilder.PARENT_INDEX_COLUMN: parent_index,
            XLSDataFrameBuilder.PARENT_TABLE_NAME_COLUMN: parent_table_name})

        # add ADDITIONAL_COLUMNS
        data_section[len(data_section)-1].update(
            dict([(column, record[column] if record.has_key(column) else None)
                  for column in self.ADDITIONAL_COLUMNS]))

    def _generate_sections(self):
        """
        Split survey questions into separate sections for each xls sheet and
        columns for each section
        """
        # clear list
        self.sections = OrderedDict()

        # dict of select multiple elements
        self.select_multiples = {}

        survey_element = self.dd.survey
        self.survey_name = get_valid_sheet_name(
            survey_element.name, self.sections.keys())
        self._create_section(
            self.survey_name, survey_element.get_abbreviated_xpath(), False)
        # build sections
        self._build_sections_recursive(self.survey_name, self.dd.get_survey())

        for section_name in self.sections:
            self.sections[section_name]['columns'] += self.ADDITIONAL_COLUMNS
        self.get_exceeds_xls_limits()

    def _build_sections_recursive(self, section_name, element, is_repeating=False):
        """Builds a section's children and recurses any repeating sections
        to build those as a separate section
        """
        for child in element.children:
            # if a section, recurse
            if isinstance(child, Section):
                new_is_repeating = isinstance(child, RepeatingSection)
                new_section_name = section_name
                # if its repeating, build a new section
                if new_is_repeating:
                    new_section_name = get_valid_sheet_name(
                        child.name, self.sections.keys())
                    self._create_section(new_section_name,
                        child.get_abbreviated_xpath(), True)

                self._build_sections_recursive(
                    new_section_name, child, new_is_repeating)
            else:
                # add to survey_sections
                if isinstance(child, Question) and not \
                        question_types_to_exclude(child.type)\
                and not child.bind.get(u"type") == MULTIPLE_SELECT_BIND_TYPE:
                        self._add_column_to_section(section_name, child)
                elif child.bind.get(u"type") == MULTIPLE_SELECT_BIND_TYPE:
                    self.select_multiples[child.get_abbreviated_xpath()] = \
                    [option.get_abbreviated_xpath() for option in
                            child.children]
                    # if select multiple, get its choices and make them
                    # columns
                    if self.split_select_multiples:
                        for option in child.children:
                            self._add_column_to_section(section_name, option)
                    else:
                        self._add_column_to_section(section_name, child)

                # split gps fields within this section
                if child.bind.get(u"type") == GEOPOINT_BIND_TYPE:
                    # add columns for geopoint components
                    for xpath in\
                        self.dd.get_additional_geopoint_xpaths(
                        child.get_abbreviated_xpath()):
                        self._add_column_to_section(section_name, xpath)

    def get_exceeds_xls_limits(self):
        if not hasattr(self, "exceeds_xls_limits"):
            self.exceeds_xls_limits = False
            if len(self.sections) > self.XLS_SHEET_COUNT_LIMIT:
                self.exceeds_xls_limits = True
            else:
                for section in self.sections.itervalues():
                    if len(section["columns"]) > self.XLS_COLUMN_COUNT_MAX:
                        self.exceeds_xls_limits = True
                        break
        return self.exceeds_xls_limits

    def _create_section(self, section_name, xpath, is_repeat):
        index = len(self.sections)
        self.sections[section_name] = {"name": section_name, "xpath": xpath,
                              "columns": [], "is_repeat": is_repeat,
                              self.CURRENT_INDEX_META: 0}

    def _add_column_to_section(self, sheet_name, column):
        section = self.sections[sheet_name]
        xpath = None
        if isinstance(column, SurveyElement):
            xpath = column.get_abbreviated_xpath()
        elif isinstance(column, basestring):
            xpath = column
        assert(xpath)
        # make sure column is not already in list
        if xpath not in section["columns"]:
            section["columns"].append(xpath)


class CSVDataFrameBuilder(AbstractDataFrameBuilder):

    def __init__(self, username, id_string, filter_query=None,
                 group_delimiter=DEFAULT_GROUP_DELIMITER,
                 split_select_multiples=True):
        super(CSVDataFrameBuilder, self).__init__(username,
            id_string, filter_query, group_delimiter, split_select_multiples)
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
                        # given the key "children/details" and nested_key/ abbreviated xpath "children/details/immunization/polio_1", generate ["children", index, "immunization/polio_1"]
                        xpaths = [
                            "%s[%s]" % (
                                nested_key[:nested_key.index(key) + len(key)],
                                index), 
                            nested_key[nested_key.index(key) + len(key)+1:]]
                        # re-create xpath the split on /
                        xpaths = "/".join(xpaths).split("/")
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
        are not considered columns
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
        # add ordered columns for select multiples
        if self.split_select_multiples:
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
            if self.split_select_multiples:
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

            # if delimetr is diferent, replace within record as well
            if self.group_delimiter != DEFAULT_GROUP_DELIMITER:
                flat_dict = dict((self.group_delimiter.join(k.split('/')), v) for k, v in flat_dict.iteritems())
            data.append(flat_dict)
        return data

    def export_to(self, file_or_path, data_frame_max_size=30000):
        from math import ceil
        # get record count
        record_count = self._query_mongo(query=self.filter_query, count=True)

        self.ordered_columns = OrderedDict()
        self._build_ordered_columns(self.dd.survey, self.ordered_columns)
        
        # pandas will only export 30k records in a dataframe to a csv - we need to create multiple 30k dataframes if required,
        # we need to go through all the records though so that we can figure out the columns we need for repeats
        datas = []
        num_data_frames = int(ceil(float(record_count)/float(data_frame_max_size)))
        for i in range(num_data_frames):
            cursor = self._query_mongo(self.filter_query,
                start=(i * data_frame_max_size), limit=data_frame_max_size)
            data = self._format_for_dataframe(cursor)
            datas.append(data)

        columns = list(chain.from_iterable([[ xpath ] if cols == None else cols\
                                            for xpath, cols in self.ordered_columns.iteritems()]))

        # use a different group delimiter if needed
        if self.group_delimiter != DEFAULT_GROUP_DELIMITER:
            columns = [self.group_delimiter.join(col.split("/")) for col in columns ]

        # add extra columns
        columns += [col for col in self.ADDITIONAL_COLUMNS]

        header = True
        if hasattr(file_or_path, 'read'):
            csv_file = file_or_path
            close = False
        else:
            csv_file = open(file_or_path, "wb")
            close = True

        for data in datas:
            writer = CSVDataFrameWriter(data, columns)
            writer.write_to_csv(csv_file, header=header)
            header = False
        if close:
            csv_file.close()

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
        for col in AbstractDataFrameBuilder.IGNORED_COLUMNS:
            if col in self.dataframe.columns:
                del(self.dataframe[col])

    def write_to_csv(self, csv_file, header=True, index=False):
        self.dataframe.to_csv(csv_file, header=header, index=index, na_rep=NA_REP,
                              encoding='utf-8')
