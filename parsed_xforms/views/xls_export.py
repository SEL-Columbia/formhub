from django.contrib.auth.decorators import permission_required
from common_tags import XFORM_ID_STRING
from parsed_xforms.models import xform_instances, DataDictionary
from collections import defaultdict
import xlwt
from django.http import HttpResponse

def _get_parsed_instances_from_mongo(id_string):
    match_id_string = {XFORM_ID_STRING : id_string}
    parsed_instances = \
        xform_instances.find(spec=match_id_string)
    return list(parsed_instances)

def _get_list_of_unique_keys(list_of_dicts):
    s = set()
    for d in list_of_dicts:
        for k in d.keys():
            s.add(k)
    return list(s)

def _sort_xpaths(xpaths, data_dictionary):
    if data_dictionary:
        # Sort the xpaths based on the order they appear in the
        # survey.
        data_dictionary.sort_xpaths(xpaths)
    else:
        # Sort the xpaths based on alphabetical order.
        xpaths.sort()

def _get_sorted_xpaths(list_of_dicts, data_dictionary):
    xpaths = _get_list_of_unique_keys(list_of_dicts)
    _sort_xpaths(xpaths, data_dictionary)
    return xpaths

DATA_DICTIONARY = u"data_dictionary"
DATA = u"data"
XPATHS = u"xpaths"

def get_data_for_spreadsheet(id_string):
    result = {}
    try:
        result[DATA_DICTIONARY] = \
            DataDictionary.objects.get(xform__id_string=id_string)
    except DataDictionary.DoesNotExist:
        resutl[DATA_DICTIONARY] = None

    result[DATA] = _get_parsed_instances_from_mongo(id_string)
    result[XPATHS] = _get_sorted_xpaths(result[DATA], result[DATA_DICTIONARY])
    return result

NUMBER_OF_COLUMNS = 256

def _split_table_into_data_sheets(table):
    sheets = defaultdict(list)
    for row in table:
        sheet_number = 0
        while sheet_number * NUMBER_OF_COLUMNS < len(row):
            start = sheet_number * NUMBER_OF_COLUMNS
            end = (sheet_number+1) * NUMBER_OF_COLUMNS
            sheets[sheet_number].append(row[start:end])
            sheet_number += 1
    result = []
    for i in range(len(sheets.keys())):
        result.append( ("Data Sheet %s" % str(i+1),
                        sheets[i]) )
    return result

def _get_headers(data_dictionary, xpaths):
    return [data_dictionary.get_variable_name(xpath) for xpath in xpaths]

def construct_worksheets(id_string):
    # data, headers, and dictionary
    dhd = get_data_for_spreadsheet(id_string)

    sheet1 = [_get_headers(dhd[DATA_DICTIONARY], dhd[XPATHS])]
    for survey in dhd[DATA]:
        row = []
        for xpath in dhd[XPATHS]:
            cell = survey.get(xpath, u"n/a")
            row.append(unicode(cell))
        sheet1.append(row)
    result = _split_table_into_data_sheets(sheet1)

    if DATA_DICTIONARY in dhd:
        sheet2 = [[u"Name", u"Label"]] + dhd[DATA_DICTIONARY]
        result.append((u"Dictionary", sheet2))
    return result

def xls_to_response(xls, fname):
    response = HttpResponse(mimetype="application/ms-excel")
    response['Content-Disposition'] = 'attachment; filename=%s' % fname
    xls.save(response)
    return response

from deny_if_unauthorized import deny_if_unauthorized

@deny_if_unauthorized()
def xls(request, id_string):
    worksheets = construct_worksheets(id_string)

    wb = xlwt.Workbook()
    for sheet_name, table in worksheets:
        ws = wb.add_sheet(sheet_name)
        for r in range(len(table)):
            for c in range(len(table[r])):
                ws.write(r, c, table[r][c])

    return xls_to_response(wb, id_string + ".xls")
