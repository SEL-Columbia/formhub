from collections import defaultdict
from pyxform import Section, Question
from parsed_xforms.models import DataDictionary
import os
from xform_manager.xform_instance_parser import xform_instance_to_dict

class XlsWriter(object):
    def __init__(self):
        self.set_file()
        self.reset_workbook()
    
    def set_file(self, file_object=None):
        """
        If the file object is None use a StringIO object.
        """
        if file_object is not None:
            self._file = file_object
        else:
            from StringIO import StringIO
            self._file = StringIO()

    def reset_workbook(self):
        import xlwt
        self._workbook = xlwt.Workbook()
        self._sheets = {}
        self._columns = defaultdict(list)
        def one(): return 1
        self._current_index = defaultdict(one)

    def add_sheet(self, name):
        sheet = self._workbook.add_sheet(name[0:20])
        self._sheets[name] = sheet

    def add_column(self, sheet_name, column_name):
        index = len(self._columns[sheet_name])
        self._sheets[sheet_name].write(0, index, column_name)
        self._columns[sheet_name].append(column_name)

    def add_row(self, sheet_name, row):
        i = self._current_index[sheet_name]
        columns = self._columns[sheet_name]
        for key in row.keys():
            if key not in columns:
                self.add_column(sheet_name, key)
        for j, column_name in enumerate(self._columns[sheet_name]):
            self._sheets[sheet_name].write(i, j, row.get(column_name, u"n/a"))
        self._current_index[sheet_name] += 1

    def add_obs(self, obs):
        self._fix_indices(obs)
        for sheet_name, rows in obs.items():
            for row in rows:
                self.add_row(sheet_name, row)

    def _fix_indices(self, obs):
        for sheet_name, rows in obs.items():
            for row in rows:
                row[u'_index'] += self._current_index[sheet_name]
                if row[u'_parent_index']==-1: continue
                i = self._current_index[row[u'_parent_table_name']]
                row[u'_parent_index'] += i

    def write_tables_to_workbook(self, tables):
        """
        tables should be a list of pairs, the first element in the
        pair is the name of the table, the second is the actual data.

        todo: figure out how to write to the xls file rather than keep
        the whole workbook in memory.
        """
        self.reset_workbook()
        for table_name, table in tables:
            self.add_sheet(table_name)
            for i, row in enumerate(table):
                for j, value in enumerate(row):
                    self._sheets[table_name].write(i,j,unicode(value))
        return self._workbook

    def save_workbook_to_file(self):
        self._workbook.save(self._file)
        return self._file


class DataDictionaryWriter(XlsWriter):
    def set_data_dictionary(self, data_dictionary):
        self._data_dictionary = data_dictionary
        self.reset_workbook()
        self._add_sheets()
        self.add_surveys()

    def _add_sheets(self):
        for e in self._data_dictionary.get_survey_elements():
            if isinstance(e, Section):
                sheet_name = e.get_name()
                self.add_sheet(sheet_name)
                for f in e.get_children():
                    if isinstance(f, Question):
                        self.add_column(sheet_name, f.get_name())

    def add_surveys(self):
        if not hasattr(self, "_dict_organizer"):
            self._dict_organizer = DictOrganizer()
        for i in self._data_dictionary.xform.surveys.iterator():
            d = xform_instance_to_dict(i.xml)
            obs = self._dict_organizer.get_observation_from_dict(d)
            self.add_obs(obs)


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


from django.http import HttpResponse
from deny_if_unauthorized import deny_if_unauthorized

@deny_if_unauthorized()
def xls_export(request, id_string):
    dd = DataDictionary.objects.get(xform__id_string=id_string)
    ddw = DataDictionaryWriter()
    ddw.set_data_dictionary(dd)
    temp_file = ddw.save_workbook_to_file()
    response = HttpResponse(mimetype='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=%s.xls' % id_string
    response.write(temp_file.getvalue())
    temp_file.close()    
    return response
