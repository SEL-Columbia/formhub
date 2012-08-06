from collections import defaultdict
from pyxform import Section, Question
from odk_viewer.models import DataDictionary
from utils.export_tools import question_types_to_exclude

class XlsWriter(object):
    def __init__(self):
        self.set_file()
        self.reset_workbook()
        self.sheet_name_limit = 30
        self._generated_sheet_name_dict = {}

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
        self._generated_sheet_name_dict = {}

    def add_sheet(self, name):
        unique_sheet_name = self._unique_name_for_xls(name)
        sheet = self._workbook.add_sheet(unique_sheet_name)
        self._sheets[unique_sheet_name] = sheet

    def add_column(self, sheet_name, column_name):
        index = len(self._columns[sheet_name])
        sheet = self._sheets.get(sheet_name)
        if sheet:
            sheet.write(0, index, column_name)
            self._columns[sheet_name].append(column_name)

    def add_row(self, sheet_name, row):
        i = self._current_index[sheet_name]
        columns = self._columns[sheet_name]
        for key in row.keys():
            if key not in columns:
                self.add_column(sheet_name, key)
        for j, column_name in enumerate(self._columns[sheet_name]):
            # leaving this untranslated as I'm not sure it's in django context
            self._sheets[sheet_name].write(i, j, row.get(column_name, u"n/a"))
        self._current_index[sheet_name] += 1

    def add_obs(self, obs):
        self._fix_indices(obs)
        for sheet_name, rows in obs.items():
            for row in rows:
                actual_sheet_name = self._generated_sheet_name_dict.get(
                        sheet_name, sheet_name)
                self.add_row(actual_sheet_name, row)

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

        TODO: figure out how to write to the xls file rather than keep
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

    def set_data_dictionary(self, data_dictionary):
        self._data_dictionary = data_dictionary
        self.reset_workbook()
        self._add_sheets()
        observations = self._data_dictionary.add_surveys()
        for obs in observations:
            self.add_obs(obs)

    def _add_sheets(self):
        for e in self._data_dictionary.get_survey_elements():
            if isinstance(e, Section):
                sheet_name = e.name
                self.add_sheet(sheet_name)
                for f in e.children:
                    if isinstance(f, Question) and\
                            not question_types_to_exclude(f.type):
                        self.add_column(sheet_name, f.name)

    def _unique_name_for_xls(self, sheet_name):
        # excel worksheet name limit seems to be 31 characters (30 to be safe)
        unique_sheet_name = sheet_name[0:self.sheet_name_limit]
        unique_sheet_name = self._generate_unique_sheet_name(unique_sheet_name)
        self._generated_sheet_name_dict[sheet_name] = unique_sheet_name
        return unique_sheet_name

    def _generate_unique_sheet_name(self, sheet_name):
        # check if sheet name exists
        if(not self._sheets.has_key(sheet_name)):
            return sheet_name
        else:
            i = 1
            unique_name = sheet_name
            while(self._sheets.has_key(unique_name)):
                number_len = len(str(i))
                allowed_name_len = self.sheet_name_limit - number_len
                # make name required len
                if(len(unique_name) > allowed_name_len):
                    unique_name = unique_name[0:allowed_name_len]
                unique_name = "{0}{1}".format(unique_name, i)
                i = i + 1
            return unique_name

