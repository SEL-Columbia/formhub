from StringIO import StringIO
import xlwt

class XlsWriter(object):
    def set_file(self, file_object=None):
        """
        If the file object is None use a StringIO object.
        """
        if file_object is not None:
            self._file = file_object
        else:
            self._file = StringIO()

    def set_tables(self, tables):
        """
        tables should be a list of pairs, the first element in the
        pair is the name of the table, the second is the actual data.

        todo: figure out how to write to the xls file rather than keep
        the whole workbook in memory.
        """
        self._tables = tables

    def get_xlwt_workbook(self):
        book = xlwt.Workbook()
        for table_name, table in self._tables:
            sheet = book.add_sheet(table_name)
            for i, row in enumerate(table):
                for j, value in enumerate(row):
                    sheet.write(i,j,unicode(value))
        return book

    def get_xls_file(self):
        work_book = self.get_xlwt_workbook()
        work_book.save(self._file)
        return self._file


class DictOrganizer(object):
    def set_dict_iterator(self, dict_iterator):
        self._dict_iterator = dict_iterator

    def set_data_dictionary(self, data_dictionary):
        self._data_dictionary = data_dictionary

    def _set_table_names(self):
        self._table_names = []
        for survey_element in self.data_dictionary.get_survey_elements():
            if isinstance(survey_element, Section):
                self._table_names.append(survey_element.get_name())

    def _mark_repeating_sections(self):
        self._repeating_section_names = []
        for survey_element in self.data_dictionary.get_survey_elements():
            if isinstance(survey_element, RepeatingSection):
                self._repeating_section_names.append(survey_element.get_name())

    # Every section will get its own table
    # I need to think of an easy way to flatten out a dictionary
    # parent name, index, table name, data
    def _yield_rows_from_dict(self, d, table_name, index=1, parent_name=u"", parent_index=0):
        result = {
            u"_parent_name" : parent_name,
            u"_parent_index" : parent_index,
            u"_table_name" : table_name,
            u"_index" : index,
            }
        for k, v in d.items():
            if type(v)!=dict and type(v)!=list:
                result[k] = v
        yield result

        for k, v in d.items():
            if type(v)==dict:
                kwargs = {
                    "d" : v,
                    "table_name" : k,
                    "index" : 1,
                    "parent_name" : table_name,
                    "parent_index" : index
                    }
                for result in self._yield_rows_from_dict(**kwargs):
                    yield result
            if type(v)==list:
                for i, item in enumerate(v):
                    kwargs = {
                        "d" : item,
                        "table_name" : k,
                        "index" : i+1,
                        "parent_name" : table_name,
                        "parent_index" : index,
                        }
                    for result in self._yield_rows_from_dict(**kwargs):
                        yield result

    def _combine_rows_into_observation(self, d):
        result = {}
        assert len(d.keys())==1
        root_name = d.keys()[0]
        for row in self._yield_rows_from_dict(d[root_name], table_name=root_name):
            table_name = row.pop(u"_table_name")
            if table_name not in result: result[table_name] = []
            result[table_name].append(row)
        return result


def export(data_dictionary, file_object, format="blah"):
    """
    Exports data from couch documents matching a given tag to a file. 
    Returns true if it finds data, otherwise nothing
    """
    schema = data_dictionary.get_shema()
    docs = [result['value'] for result in db.view("couchexport/schema_index", key=schema_index).all()]
    tables = format_tables(create_intermediate_tables(docs,schema))
    _export_excel_2007(tables).save(file_object)

def fit_to_schema(doc, schema):

    def log(msg):
        raise Exception("doc-schema mismatch: %s" % msg)

    if schema is None:
        if doc:
            log("%s is not null" % doc)
        return None
    if isinstance(schema, list):
        if not doc:
            doc = []
        if not isinstance(doc, list):
            return fit_to_schema([doc], schema)
        answ = []
        schema_, = schema
        for doc_ in doc:
            answ.append(fit_to_schema(doc_, schema_))
        return answ
    if isinstance(schema, dict):
        if not doc:
            doc = {}
        doc_keys = set(doc.keys())
        schema_keys = set(schema.keys())
        if doc_keys - schema_keys:
            log("doc has keys not in schema: %s" % (', '.join(doc_keys - schema_keys)))
        answ = {}
        for key in schema:
            #if schema[key] == unknown_type: continue
            if doc.has_key(key):
                answ[key] = fit_to_schema(doc.get(key), schema[key])
            else:
                answ[key] = render_never_was(schema[key])
        return answ
    if schema == "string":
        if not doc:
            doc = ""
        if not isinstance(doc, basestring):
        #log("%s is not a string" % doc)
            doc = unicode(doc)
        return doc


def create_intermediate_tables(docs, schema, integer='#'):
    def lookup(doc, keys):
        for key in keys:
            doc = doc[key]
        return doc
    def split_path(path):
        table = []
        column = []
        id = []
        for k in path:
            if isinstance(k, basestring):
                column.append(k)
            else:
                table.extend(column)
                table.append(integer)
                column = []
                id.append(k)
        return (tuple(table), tuple(column), tuple(id))
    schema = [schema]
    docs = fit_to_schema(docs, schema)
    #first, flatten documents
    queue = [()]
    leaves = []
    while queue:
        path = queue.pop()
        d = lookup(docs, path)
        if isinstance(d, dict):
            for key in d:
                queue.append(path + (key,))
        elif isinstance(d, list):
            for i,_ in enumerate(d):
                queue.append(path + (i,))
        elif d != list_never_was:
            leaves.append((split_path(path), d))
    leaves.sort()
    tables = {}
    for (table_name, column_name, id), val in leaves:
        table = tables.setdefault(table_name, {})
        row = table.setdefault(id, {})
        row[column_name] = val

    return tables

def nice(column_name):
    return "/".join(column_name)

def format_tables(tables, id_label='id', separator='.'):
    answ = []
    for table_name, table in sorted(tables.items()):
        new_table = []
        keys = sorted(table.items()[0][1].keys()) # the keys for every row are the same
        header = [id_label]
        for key in keys:
            header.append(separator.join(key))
        new_table.append(header)
        for id, row in sorted(table.items()):
            new_row = []
            new_row.append(separator.join(map(unicode,id)))
            for key in keys:
                new_row.append(row[key])
            new_table.append(new_row)
        answ.append((separator.join(table_name), new_table))
    return answ

def export_csv(tables):
    "this function isn't ready to use because of how it deals with files"
    for table_name, table in tables:
        writer = csv.writer(open("csv_test/" + table_name+'.csv', 'w'), dialect=csv.excel)
        for row in table:
            writer.writerow([x if '"' not in x else "" for x in row])

def _export_excel(tables):
    try:
        import xlwt
    except ImportError:
        raise Exception("It doesn't look like this machine is configured for "
                        "excel export. To export to excel you have to run the "
                        "command:  easy_install xlutils")
    book = xlwt.Workbook()
    for table_name, table in tables:
        # this is in case the first 20 characters are the same, but we	
        # should do something smarter.	
        #sheet = book.add_sheet(table_name[-20:])
        hack_table_name_prefix = table_name[-20:]
        hack_table_name = hack_table_name_prefix[0:10] + hashlib.sha1(table_name).hexdigest()[0:10]
        sheet = book.add_sheet(hack_table_name)
        for i,row in enumerate(table):
            for j,val in enumerate(row):
                sheet.write(i,j,unicode(val))
    return book


from django.http import HttpResponse
import json

def xls(data_dictionary):
    """
    Download all data associated with this data dictionary.
    """
    if export(data_dictionary, tmp, format=Format.XLS):
        response = HttpResponse(mimetype='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename=%s.%s' % (export_tag, format)
        response.write(tmp.getvalue())
        tmp.close()
        return response
    else:
        return HttpResponse("Sorry, there was no data found for the tag '%s'." % export_tag)
