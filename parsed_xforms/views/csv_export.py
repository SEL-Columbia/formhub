import codecs
import os
import re

class CsvWriter(object):
    """
    Gosh darn csv package doesn't work with unicode.
    
    This class is a simple wrapper around csv.writer. It takes a row
    iterator and a path to the file to write.
    This class takes a dict iterator, a key comparator (for sorting
    the keys), and a function to rename the keys.
    """
    def __init__(self):
        self._dict_iterator = []
        self._keys = []
        self._key_comparator = cmp
        self._key_rename_function = lambda x: x

    def set_generator_function(self, generator_function):
        """
        Unfortunately there doesn't seem to be a way to rewind a
        generator, so instead of just passing a generator as my
        dict_iterator, I'm passing the generator function so we can
        get a new generator after we run through the first.
        """
        self._generator_function = generator_function
        self._reset_dict_iterator()
        self._create_list_of_keys()

    # def set_dict_iterator(self, dict_iterator):
    #     self._dict_iterator = dict_iterator
    #     self._create_list_of_keys()

    def _reset_dict_iterator(self):
        self._dict_iterator = self._generator_function()

    def _create_list_of_keys(self):
        key_set = set()
        for d in self._dict_iterator:
            for k in d.iterkeys():
                key_set.add(k)
        self._keys = list(key_set)
        self._reset_dict_iterator()

    def set_key_comparator(self, key_comparator):
        self._key_comparator = key_comparator

    def _sort_keys(self):
        self._keys.sort(cmp=self._key_comparator)

    def set_key_rename_function(self, key_rename_function):
        self._key_rename_function = key_rename_function

    def _ensure_directory_exists(self, path):
        abspath = os.path.abspath(path)
        directory = os.path.dirname(abspath)
        if not os.path.exists(directory):
            os.makedirs(directory)

    def write_to_file(self, path):
        self._ensure_directory_exists(path)
        self._file_object = codecs.open(path, mode="w", encoding="utf-8")

        self._sort_keys()
        headers = [self._key_rename_function(k) for k in self._keys]
        self._write_row(headers)

        for d in self._dict_iterator:
            # todo: figure out how to use csv.writer with unicode
            self._write_row([d.get(k, u"n/a") for k in self._keys])
        self._reset_dict_iterator()

        self._file_object.close()

    def _write_row(self, row):
        quote_escaped_row = []
        for cell in row:
            cell_string = unicode(cell)
            cell_string = re.sub(ur"\s+", u" ", cell_string)
            if u',' in cell_string:
                quote_escaped_row.append(u'"%s"' % cell_string)
            else:
                quote_escaped_row.append(cell_string)
        row_string = u",".join(quote_escaped_row)
        self._file_object.writelines([row_string, u"\n"])


from parsed_xforms.models import DataDictionary

class DataDictionaryWriter(CsvWriter):

    def __init__(self):
        super(DataDictionaryWriter, self).__init__()
        self._data_dictionary = None

    def set_data_dictionary(self, data_dictionary):
        self._data_dictionary = data_dictionary

        generator_function = data_dictionary.get_data_for_excel
        self.set_generator_function(generator_function)

        key_comparator = data_dictionary.get_column_key_cmp()
        self.set_key_comparator(key_comparator)

        key_rename_function = data_dictionary.get_variable_name
        self.set_key_rename_function(key_rename_function)

# http://djangosnippets.org/snippets/365/
from django.http import HttpResponse
from django.core.servers.basehttp import FileWrapper

def send_file(path, content_type):
    """                                                                         
    Send a file through Django without loading the whole file into              
    memory at once. The FileWrapper will turn the file object into an           
    iterator for chunks of 8KB.                                                 
    """
    wrapper = FileWrapper(file(path))
    response = HttpResponse(wrapper, content_type=content_type)
    response['Content-Length'] = os.path.getsize(path)
    return response

from deny_if_unauthorized import deny_if_unauthorized

@deny_if_unauthorized()
def csv_export(request, id_string):
    dd = DataDictionary.objects.get(xform__id_string=id_string)
    ddw = DataDictionaryWriter()
    ddw.set_data_dictionary(dd)
    this_directory = os.path.dirname(__file__)
    file_path = os.path.join(this_directory, "csvs", id_string + ".csv")
    ddw.write_to_file(file_path)
    return send_file(path=file_path, content_type="application/csv")
