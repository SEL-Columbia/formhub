import xlwt
from collections import defaultdict

class ExcelWriter(object):
    """
    This class is a simple wrapper around xlwt. It takes a list of
    dictionaries (data) and a list of headers, and constructs an excel
    workbook from those.
    """

    def __init__(self, data, column_keys, rename_function):
        self._set_data(data)
        self._set_column_keys(column_keys)
        self._set_rename_function(rename_function)
        self._setup_worksheets()
        self._rename_columns()

    def _set_data(self, data):
        """
        data is a list of dictionaries, each dictionary describes a
        row in the spreadsheet
        """
        assert type(data)==list
        for d in data: assert type(d)==dict
        self._data = data

    def _set_column_keys(self, column_keys):
        assert type(column_keys)==list
        for header in column_keys: assert type(header)==unicode
        self._column_keys = column_keys

    def _set_rename_function(self, rename_function):
        assert callable(rename_function)
        self._get_column_name = rename_function

    def _setup_worksheets(self):
        # todo: could break this into two steps as I had before:
        # 1. construct one giant table of the data
        # 2. split that giant table up into tables with at most 256
        #    columns
        max_number_of_columns = 256

        self._sheets = defaultdict(list)
        for d in self._data:
            sheet_number = 0
            while sheet_number * max_number_of_columns < len(self._column_keys):
                sheet_name = u"Data Sheet %s" % unicode(sheet_number)
                if len(self._sheets[sheet_name])==0:
                    start = sheet_number * max_number_of_columns
                    end = (sheet_number+1) * max_number_of_columns
                    sheet_column_keys = self._column_keys[start:end]
                    self._sheets[sheet_name].append(sheet_column_keys)
                row = [d.get(header) for header in self._sheets[sheet_name][0]]
                self._sheets[sheet_name].append(row)
                sheet_number += 1

    def _rename_columns(self):
        for sheet in self._sheets.values():
            for i in range(len(sheet[0])):
                sheet[0][i] = self._get_column_name(sheet[0][i])

    def set_sheet(self, name, table):
        self._sheets[name] = table

    def get_workbook(self):
        self._wb = xlwt.Workbook()
        for sheet_name, table in self._sheets.items():
            ws = self._wb.add_sheet(sheet_name)
            for i in range(len(table)):
                for j in range(len(table[i])):
                    ws.write(i, j, unicode(table[i][j]))
        return self._wb


from parsed_xforms.models import DataDictionary

class DataDictionaryWriter(ExcelWriter):

    def __init__(self, data_dictionary):
        assert type(data_dictionary)==DataDictionary
        self._data_dictionary = data_dictionary
        data = data_dictionary.get_data_for_excel()
        column_keys = data_dictionary.get_column_keys_for_excel()
        rename_function = data_dictionary.get_variable_name
        ExcelWriter.__init__(self, data, column_keys, rename_function)

    def _add_data_dictionary_sheet(self):
        sheet = [[u"Name", u"Label"]]
        for e in self._data_dictionary.get_survey_elements():
            sheet.append([e.get_abbreviated_xpath(), e.get_label()])
        self.set_sheet(u"Dictionary", sheet)


from django.http import HttpResponse

def xls_to_response(xls, fname):
    response = HttpResponse(mimetype="application/ms-excel")
    response['Content-Disposition'] = 'attachment; filename=%s' % fname
    xls.save(response)
    return response

from deny_if_unauthorized import deny_if_unauthorized

@deny_if_unauthorized()
def xls(request, id_string):
    dictionary = \
        DataDictionary.objects.get(xform__id_string=id_string)
    writer = DataDictionaryWriter(dictionary)
    workbook = writer.get_workbook()
    return xls_to_response(workbook, id_string + ".xls")
