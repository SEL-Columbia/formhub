import os
from datetime import datetime
from django.core.files.base import File
from django.core.files.temp import NamedTemporaryFile
from django.core.files.storage import get_storage_class
import re
from odk_logger.models import XForm


QUESTION_TYPES_TO_EXCLUDE = [
    u'note',
]


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


def _df_builder_for_export_type(export_type, username, id_string,
                                filter_query=None):
    from odk_viewer.pandas_mongo_bridge import XLSDataFrameBuilder,\
        CSVDataFrameBuilder
    from odk_viewer.models import Export

    if export_type == Export.XLS_EXPORT:
        return XLSDataFrameBuilder(username, id_string, filter_query)
    elif export_type == Export.CSV_EXPORT:
        return CSVDataFrameBuilder(username, id_string, filter_query)
    else:
        raise ValueError


def generate_export(export_type, extension, username, id_string,
                    export_id = None, filter_query=None):
    """
    Create appropriate export object given the export type
    """
    from odk_viewer.models import Export

    xform = XForm.objects.get(user__username=username, id_string=id_string)
    df_builder = _df_builder_for_export_type(export_type, username, id_string,
        filter_query)
    if hasattr(df_builder, 'get_exceeds_xls_limits')\
            and df_builder.get_exceeds_xls_limits():
        extension = 'xlsx'

    temp_file = NamedTemporaryFile(suffix=("." + extension))
    df_builder.export_to(temp_file.name)
    basename = "%s_%s" % (id_string,
                             datetime.now().strftime("%Y_%m_%d_%H_%M_%S"))
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
    # create export object
    export, is_new = Export.objects.get_or_create(id=export_id, xform=xform,
        export_type=export_type)
    dir_name, basename = os.path.split(export_filename)
    export.filename = basename
    export.save()
    return export


def should_create_new_export(xform, export_type):
    from odk_viewer.models import Export
    if Export.objects.filter(xform=xform, export_type=export_type).count() == 0\
            or Export.exports_outdated(xform, export_type=export_type):
        return True
    return False

def increment_index_in_filename(filename):
    """
    filename should be in the form file.ext or file-2.ext - we check for the dash and index and increment appropriately
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