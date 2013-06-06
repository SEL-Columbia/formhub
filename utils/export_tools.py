import os
import re
import csv
from openpyxl.workbook import Workbook
from openpyxl.writer.excel import ExcelWriter
from datetime import datetime
from django.conf import settings
from pyxform.section import Section, RepeatingSection
from pyxform.question import Question
from django.core.files.base import File
from django.core.files.temp import NamedTemporaryFile
from django.core.files.storage import get_storage_class
from django.contrib.auth.models import User
from django.shortcuts import render_to_response
from odk_logger.models import XForm, Attachment
from utils.viewer_tools import create_attachments_zipfile
from utils.viewer_tools import image_urls
from zipfile import ZipFile
from common_tags import ID, XFORM_ID_STRING, STATUS, ATTACHMENTS, GEOLOCATION,\
    BAMBOO_DATASET_ID, DELETEDAT, USERFORM_ID
from odk_viewer.models.parsed_instance import _is_invalid_for_mongo,\
    _encode_for_mongo, dict_for_mongo


# this is Mongo Collection where we will store the parsed submissions
xform_instances = settings.MONGO_DB.instances

QUESTION_TYPES_TO_EXCLUDE = [
    u'note',
]
# the bind type of select multiples that we use to compare
MULTIPLE_SELECT_BIND_TYPE = u"select"
GEOPOINT_BIND_TYPE = u"geopoint"


def question_types_to_exclude(_type):
    return _type in QUESTION_TYPES_TO_EXCLUDE


class DictOrganizer(object):
    def set_dict_iterator(self, dict_iterator):
        self._dict_iterator = dict_iterator

    # Every section will get its own table
    # I need to think of an easy way to flatten out a dictionary
    # parent name, index, table name, data
    def _build_obs_from_dict(self, d, obs, table_name,
                             parent_table_name, parent_index):
        if table_name not in obs:
            obs[table_name] = []
        this_index = len(obs[table_name])
        obs[table_name].append({
            u"_parent_table_name" : parent_table_name,
            u"_parent_index" : parent_index,
            })
        for k, v in d.items():
            if type(v)!=dict and type(v)!=list:
                assert k not in obs[table_name][-1]
                obs[table_name][-1][k] = v
        obs[table_name][-1][u"_index"] = this_index

        for k, v in d.items():
            if type(v)==dict:
                kwargs = {
                    "d" : v,
                    "obs" : obs,
                    "table_name" : k,
                    "parent_table_name" : table_name,
                    "parent_index" : this_index
                    }
                self._build_obs_from_dict(**kwargs)
            if type(v)==list:
                for i, item in enumerate(v):
                    kwargs = {
                        "d" : item,
                        "obs" : obs,
                        "table_name" : k,
                        "parent_table_name" : table_name,
                        "parent_index" : this_index,
                        }
                    self._build_obs_from_dict(**kwargs)
        return obs

    def get_observation_from_dict(self, d):
        result = {}
        assert len(d.keys())==1
        root_name = d.keys()[0]
        kwargs = {
            "d" : d[root_name],
            "obs" : result,
            "table_name" : root_name,
            "parent_table_name" : u"",
            "parent_index" : -1,
            }
        self._build_obs_from_dict(**kwargs)
        return result


def dict_to_joined_export(data, index, indices, name):
    """
    Converts a dict into one or more tabular datasets
    """
    output = {}
    # TODO: test for _geolocation and attachment lists
    if isinstance(data, dict):
        for key, val in data.iteritems():
            if isinstance(val, list):
                output[key] = []
                for child in val:
                    if not indices.has_key(key):
                        indices[key] = 0
                    indices[key] += 1
                    child_index = indices[key]
                    new_output = dict_to_joined_export(
                        child, child_index, indices, key)
                    d = {'index': child_index, 'parent_index': index, 'parent_table': name}
                    # iterate over keys within new_output and append to main output
                    for out_key, out_val in new_output.iteritems():
                        if isinstance(out_val, list):
                            if not output.has_key(out_key):
                                output[out_key] = []
                            output[out_key].extend(out_val)
                        else:
                            d.update(out_val)
                    output[key].append(d)
            else:
                if name not in output:
                    output[name] = {}
                output[name][key] = val#str(val)
    return output


class ExportBuilder(object):
    IGNORED_COLUMNS = [XFORM_ID_STRING, STATUS, ATTACHMENTS, GEOLOCATION,
                       BAMBOO_DATASET_ID, DELETEDAT]
    EXTRA_FIELDS = [ID, 'index', 'parent_index', 'parent_table']
    SPLIT_SELECT_MULTIPLES = True

    # column group delimiters
    GROUP_DELIMITER_SLASH = '/'
    GROUP_DELIMITER_DOT = '.'
    GROUP_DELIMITER = GROUP_DELIMITER_SLASH
    GROUP_DELIMITERS = [GROUP_DELIMITER_SLASH, GROUP_DELIMITER_DOT]

    XLS_SHEET_NAME_MAX_CHARS = 31

    @classmethod
    def format_field_title(cls, abbreviated_xpath, field_delimiter):
        if field_delimiter != '/':
            return field_delimiter.join(abbreviated_xpath.split('/'))
        return abbreviated_xpath

    def set_survey(self, survey):
        from odk_viewer.models import DataDictionary

        def build_sections(
                current_section, survey_element, sections, select_multiples,
                gps_fields, encoded_fields, field_delimiter='/'):
            for child in survey_element.children:
                current_section_name = current_section['name']
                # if a section, recurs
                if isinstance(child, Section):
                    # if its repeating, build a new section
                    if isinstance(child, RepeatingSection):
                        # section_name in recursive call changes
                        section = {
                            'name': child.get_abbreviated_xpath(),
                            'elements': []}
                        self.sections.append(section)
                        build_sections(
                            section, child, sections, select_multiples,
                            gps_fields, encoded_fields, field_delimiter)
                    else:
                        # its a group, recurs using the same section
                        build_sections(
                            current_section, child, sections, select_multiples,
                            gps_fields, encoded_fields, field_delimiter)
                elif isinstance(child, Question) and child.bind.get(u"type")\
                        not in QUESTION_TYPES_TO_EXCLUDE:
                    # add to survey_sections
                    if isinstance(child, Question):
                        child_xpath = child.get_abbreviated_xpath()
                        current_section['elements'].append({
                            'title': ExportBuilder.format_field_title(
                                child.get_abbreviated_xpath(), field_delimiter),
                            'xpath': child_xpath})

                        if _is_invalid_for_mongo(child.name):
                            if current_section_name not in encoded_fields:
                                encoded_fields[current_section_name] = {}
                            encoded_fields[current_section_name].update(
                                {child_xpath: _encode_for_mongo(child_xpath)})

                    # if its a select multiple, make columns out of its choices
                    if child.bind.get(u"type") == MULTIPLE_SELECT_BIND_TYPE:
                        current_section['elements'].extend(
                            [{
                                'title': ExportBuilder.format_field_title(
                                    c.get_abbreviated_xpath(),
                                    field_delimiter),
                                'xpath': c.get_abbreviated_xpath()}
                                for c in child.children])
                        select_multiples[current_section_name] =\
                            {
                                child.get_abbreviated_xpath():
                                [
                                    c.get_abbreviated_xpath() for
                                    c in child.children
                                ]
                            }

                    # split gps fields within this section
                    if child.bind.get(u"type") == GEOPOINT_BIND_TYPE:
                        # add columns for geopoint components
                        xpaths = DataDictionary.get_additional_geopoint_xpaths(
                            child.get_abbreviated_xpath())
                        current_section['elements'].extend(
                            [
                                {
                                    'title': ExportBuilder.format_field_title(
                                        xpath, field_delimiter),
                                    'xpath': xpath
                                }
                                for xpath in xpaths
                            ])
                        gps_fields[current_section_name] =\
                            {
                                child.get_abbreviated_xpath(): xpaths
                            }

        self.survey = survey
        self.select_multiples = {}
        self.gps_fields = {}
        self.encoded_fields = {}
        main_section = {'name': survey.name, 'elements': []}
        self.sections = [main_section]
        build_sections(
            main_section, self.survey, self.sections,
            self.select_multiples, self.gps_fields, self.encoded_fields,
            self.GROUP_DELIMITER)

    def section_by_name(self, name):
        matches = filter(lambda s: s['name'] == name, self.sections)
        assert(len(matches) == 1)
        return matches[0]

    @classmethod
    def split_select_multiples(cls, row, select_multiples):
        # for each select_multiple, get the associated data and split it
        for xpath, choices in select_multiples.iteritems():
            # get the data matching this xpath
            data = row.get(xpath)
            selections = []
            if data:
                selections = [
                    '{0}/{1}'.format(
                        xpath, selection) for selection in data.split(',')]
            row.update(
                dict([(choice, choice in selections) for choice in choices]))
        return row

    @classmethod
    def split_gps_components(cls, row, gps_fields):
        # for each gps_field, get associated data and split it
        for xpath, gps_components in gps_fields.iteritems():
            data = row.get(xpath)
            if data:
                gps_parts = data.split()
                if len(gps_parts) > 0:
                    row.update(zip(gps_components, gps_parts))
        return row

    @classmethod
    def decode_mongo_encoded_fields(cls, row, encoded_fields):
        # for each gps_field, get associated data and split it
        for xpath, encoded_xpath in encoded_fields.iteritems():
            if row.get(encoded_xpath):
                val = row.pop(encoded_xpath)
                row.update({xpath: val})
        return row

    def pre_process_row(self, row, section):
        """
        Split select multiples, gps and decode . and $
        """
        if self.SPLIT_SELECT_MULTIPLES and\
                section in self.select_multiples:
            row = ExportBuilder.split_select_multiples(
                row, self.select_multiples[section])

        if section in self.gps_fields:
            row = ExportBuilder.split_gps_components(
                row, self.gps_fields[section])

        if section in self.encoded_fields:
            row = ExportBuilder.split_gps_components(
                row, self.encoded_fields[section])

        return row

    def to_zipped_csv(self, path, data, *args):
        def write_row(row, csv_writer, fields):
            csv_writer.writerow(
                [u"{0}".format(row.get(field, '')).encode('utf-8')
                 for field in fields])

        csv_defs = {}
        for section in self.sections:
            csv_file = NamedTemporaryFile(suffix=".csv")
            csv_writer = csv.writer(csv_file)
            csv_defs[section['name']] = {
                'csv_file': csv_file, 'csv_writer': csv_writer}

        # write headers
        for section in self.sections:
            fields = [
                element['title'] for element in
                section['elements']] + self.EXTRA_FIELDS
            csv_defs[section['name']]['csv_writer'].writerow(fields)

        index = 1
        indices = {}
        survey_name = self.survey.name
        for d in data:
            output = dict_to_joined_export(d, index, indices, survey_name)
            # attach meta fields (index, parent_index, parent_table)
            # output has keys for every section
            if survey_name not in output:
                output[survey_name] = {}
            output[survey_name]['index'] = index
            for section in self.sections:
                # get data for this section and write to csv
                section_name = section['name']
                csv_def = csv_defs[section_name]
                fields = [
                    element['xpath'] for element in
                    section['elements']] + self.EXTRA_FIELDS
                csv_writer = csv_def['csv_writer']
                # section name might not exist within the output, e.g. data was
                # not provided for said repeat - write test to check this
                row = output.get(section_name, None)
                if type(row) == dict:
                    write_row(
                        self.pre_process_row(row, section_name),
                        csv_writer, fields)
                elif type(row) == list:
                    for child_row in row:
                        write_row(
                            self.pre_process_row(child_row, section_name),
                            csv_writer, fields)
            index += 1

        # write zipfile
        with ZipFile(path, 'w') as zip_file:
            for section_name, csv_def in csv_defs.iteritems():
                csv_file = csv_def['csv_file']
                csv_file.seek(0)
                zip_file.write(
                    csv_file.name, "_".join(section_name.split("/")) + ".csv")

        # close files when we are done
        for section_name, csv_def in csv_defs.iteritems():
            csv_def['csv_file'].close()

    @classmethod
    def get_valid_sheet_name(cls, desired_name, work_sheet_titles):
        # a sheet name has to be <= 31 characters and not a duplicate of an
        # existing sheet
        # truncate sheet_name to XLSDataFrameBuilder.SHEET_NAME_MAX_CHARS
        new_sheet_name = unique_sheet_name = \
            desired_name[:cls.XLS_SHEET_NAME_MAX_CHARS]

        # make sure its unique within the list
        i = 1
        generated_name = new_sheet_name
        while generated_name in work_sheet_titles:
            digit_length = len(str(i))
            allowed_name_len = cls.XLS_SHEET_NAME_MAX_CHARS - \
                digit_length
            # make name the required len
            if len(generated_name) > allowed_name_len:
                generated_name = generated_name[:allowed_name_len]
            generated_name = "{0}{1}".format(generated_name, i)
            i += 1
        return generated_name

    def to_xls_export(self, path, data, *args):
        def write_row(data, work_sheet, fields):
            work_sheet.append([data.get(f) for f in fields])

        wb = Workbook(optimized_write=True)
        work_sheets = {}
        work_sheet_titles = []
        for section in self.sections:
            section_name = section['name']
            work_sheet_title = ExportBuilder.get_valid_sheet_name(
                "_".join(section_name.split("/")), work_sheet_titles)
            work_sheet_titles.append(work_sheet_title)
            work_sheets[section_name] = wb.create_sheet(
                title=work_sheet_title)

        # write the headers
        for section in self.sections:
            section_name = section['name']
            headers = [
                element['title'] for element in
                section['elements']] + self.EXTRA_FIELDS
            # get the worksheet
            ws = work_sheets[section_name]
            ws.append(headers)

        index = 1
        indices = {}
        survey_name = self.survey.name
        for d in data:
            output = dict_to_joined_export(d, index, indices, survey_name)
            # attach meta fields (index, parent_index, parent_table)
            # output has keys for every section
            if survey_name not in output:
                output[survey_name] = {}
            output[survey_name]['index'] = index
            for section in self.sections:
                # get data for this section and write to xls
                section_name = section['name']
                fields = [
                    element['xpath'] for element in
                    section['elements']] + self.EXTRA_FIELDS

                ws = work_sheets[section_name]
                # section might not exist within the output, e.g. data was
                # not provided for said repeat - write test to check this
                row = output.get(section_name, None)
                if type(row) == dict:
                    write_row(
                        self.pre_process_row(row, section_name),
                        ws, fields)
                elif type(row) == list:
                    for child_row in row:
                        write_row(
                            self.pre_process_row(child_row, section_name),
                            ws, fields)
            index += 1

        wb.save(filename=path)

    def to_flat_csv_export(
            self, path, data, username, id_string, filter_query):
        from odk_viewer.pandas_mongo_bridge import CSVDataFrameBuilder

        csv_builder = CSVDataFrameBuilder(
            username, id_string, filter_query, self.GROUP_DELIMITER,
            self.SPLIT_SELECT_MULTIPLES)
        csv_builder.export_to(path)


def dict_to_flat_export(d, parent_index=0):
    pass


def generate_export(export_type, extension, username, id_string,
                    export_id=None, filter_query=None, group_delimiter='/',
                    split_select_multiples=True):
    """
    Create appropriate export object given the export type
    """
    from odk_viewer.models import Export
    export_type_func_map = {
        Export.XLS_EXPORT: 'to_xls_export',
        Export.CSV_EXPORT: 'to_flat_csv_export',
        Export.CSV_ZIP_EXPORT: 'to_zipped_csv',
    }

    xform = XForm.objects.get(user__username=username, id_string=id_string)

    # query mongo for the cursor
    records = query_mongo(username, id_string, filter_query)

    export_builder = ExportBuilder()
    export_builder.GROUP_DELIMITER = group_delimiter
    export_builder.SPLIT_SELECT_MULTIPLES = split_select_multiples
    export_builder.set_survey(xform.data_dictionary().survey)

    temp_file = NamedTemporaryFile(suffix=("." + extension))

    # get the export function by export type
    func = getattr(export_builder, export_type_func_map[export_type])
    func.__call__(
        temp_file.name, records, username, id_string, filter_query)

    # generate filename
    basename = "%s_%s" % (
        id_string, datetime.now().strftime("%Y_%m_%d_%H_%M_%S"))
    filename = basename + "." + extension

    # check filename is unique
    while not Export.is_filename_unique(xform, filename):
        filename = increment_index_in_filename(filename)

    file_path = os.path.join(
        username,
        'exports',
        id_string,
        export_type,
        filename)

    # TODO: if s3 storage, make private - how will we protect local storage??
    storage = get_storage_class()()
    # seek to the beginning as required by storage classes
    temp_file.seek(0)
    export_filename = storage.save(
        file_path,
        File(temp_file, file_path))
    temp_file.close()

    dir_name, basename = os.path.split(export_filename)

    # get or create export object
    if(export_id):
        export = Export.objects.get(id=export_id)
    else:
        export = Export(xform=xform, export_type=export_type)
    export.filedir = dir_name
    export.filename = basename
    export.internal_status = Export.SUCCESSFUL
    # dont persist exports that have a filter
    if filter_query == None:
        export.save()
    return export


def query_mongo(username, id_string, query=None, hide_deleted=True):
    if query is None:
        query = {}
    query = dict_for_mongo(query)
    query[USERFORM_ID] = u'{0}_{1}'.format(username, id_string)
    if hide_deleted:
        #display only active elements
        deleted_at_query = {
            "$or": [{"_deleted_at": {"$exists": False}},
                    {"_deleted_at": None}]}
        # join existing query with deleted_at_query on an $and
        query = {"$and": [query, deleted_at_query]}
    return xform_instances.find(query)


def should_create_new_export(xform, export_type):
    from odk_viewer.models import Export
    if Export.objects.filter(xform=xform, export_type=export_type).count() == 0\
            or Export.exports_outdated(xform, export_type=export_type):
        return True
    return False


def newset_export_for(xform, export_type):
    """
    Make sure you check that an export exists before calling this,
    it will a DoesNotExist exception otherwise
    """
    from odk_viewer.models import Export
    return Export.objects.filter(xform=xform, export_type=export_type)\
           .latest('created_on')


def increment_index_in_filename(filename):
    """
    filename should be in the form file.ext or file-2.ext - we check for the
    dash and index and increment appropriately
    """
    # check for an index i.e. dash then number then dot extension
    regex = re.compile(r"(.+?)\-(\d+)(\..+)")
    match = regex.match(filename)
    if match:
        basename = match.groups()[0]
        index = int(match.groups()[1]) + 1
        ext = match.groups()[2]
    else:
        index = 1
        # split filename from ext
        basename, ext = os.path.splitext(filename)
    new_filename = "%s-%d%s" % (basename, index, ext)
    return new_filename


def generate_attachments_zip_export(
        export_type, extension, username, id_string, export_id = None,
        filter_query=None):
    from odk_viewer.models import Export

    xform = XForm.objects.get(user__username=username, id_string=id_string)
    attachments = Attachment.objects.filter(instance__xform=xform)
    zip_file = create_attachments_zipfile(attachments)
    basename = "%s_%s" % (id_string,
                             datetime.now().strftime("%Y_%m_%d_%H_%M_%S"))
    filename = basename + "." + extension
    file_path = os.path.join(
        username,
        'exports',
        id_string,
        export_type,
        filename)

    storage = get_storage_class()()
    temp_file = open(zip_file)
    export_filename = storage.save(
        file_path,
        File(temp_file, file_path))
    temp_file.close()

    dir_name, basename = os.path.split(export_filename)

    # get or create export object
    if(export_id):
        export = Export.objects.get(id=export_id)
    else:
        export = Export.objects.create(xform=xform,
            export_type=export_type)

    export.filedir = dir_name
    export.filename = basename
    export.internal_status = Export.SUCCESSFUL
    export.save()
    return export


def generate_kml_export(
        export_type, extension, username, id_string, export_id = None,
        filter_query=None):
    from odk_viewer.models import Export

    user = User.objects.get(username=username)
    xform = XForm.objects.get(user__username=username, id_string=id_string)
    response = render_to_response(
        'survey.kml', {'data': kml_export_data(id_string, user)})

    basename = "%s_%s" % (id_string,
                             datetime.now().strftime("%Y_%m_%d_%H_%M_%S"))
    filename = basename + "." + extension
    file_path = os.path.join(
        username,
        'exports',
        id_string,
        export_type,
        filename)

    storage = get_storage_class()()
    temp_file = NamedTemporaryFile(suffix=extension)
    temp_file.write(response.content)
    temp_file.seek(0)
    export_filename = storage.save(
        file_path,
        File(temp_file, file_path))
    temp_file.close()

    dir_name, basename = os.path.split(export_filename)

    # get or create export object
    if(export_id):
        export = Export.objects.get(id=export_id)
    else:
        export = Export.objects.create(xform=xform,
            export_type=export_type)

    export.filedir = dir_name
    export.filename = basename
    export.internal_status = Export.SUCCESSFUL
    export.save()

    return export


def kml_export_data(id_string, user):
    from odk_viewer.models import DataDictionary, ParsedInstance
    dd = DataDictionary.objects.get(id_string=id_string,
                                    user=user)
    pis = ParsedInstance.objects.filter(instance__user=user,
                                        instance__xform__id_string=id_string,
                                        lat__isnull=False, lng__isnull=False)
    data_for_template = []

    labels = {}

    def cached_get_labels(xpath):
        if xpath in labels.keys():
            return labels[xpath]
        labels[xpath] = dd.get_label(xpath)
        return labels[xpath]

    for pi in pis:
        # read the survey instances
        data_for_display = pi.to_dict()
        xpaths = data_for_display.keys()
        xpaths.sort(cmp=pi.data_dictionary.get_xpath_cmp())
        label_value_pairs = [
            (cached_get_labels(xpath),
             data_for_display[xpath]) for xpath in xpaths
            if not xpath.startswith(u"_")]
        table_rows = []
        for key, value in label_value_pairs:
            table_rows.append('<tr><td>%s</td><td>%s</td></tr>' % (key, value))
        img_urls = image_urls(pi.instance)
        img_url = img_urls[0] if img_urls else ""
        data_for_template.append({
            'name': id_string,
            'id': pi.id,
            'lat': pi.lat,
            'lng': pi.lng,
            'image_urls': img_urls,
            'table': '<table border="1"><a href="#"><img width="210" '
                     'class="thumbnail" src="%s" alt=""></a>%s'
                     '</table>' % (img_url, ''.join(table_rows))})
    return data_for_template
