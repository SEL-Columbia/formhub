import codecs
import os
import re


class CsvWriter(object):
    """
    The csv library doesn't handle unicode strings, so we've written
    our own here.

    This class takes a generator function to iterate through all the
    dicts of data we wish to write to csv. This class also takes a key
    comparator (for sorting the keys), and a function to rename the
    headers.
    """
    def __init__(self, dict_iterator, keys, key_rename_function):
        self._dict_iterator = dict_iterator
        self._keys = keys
        self._key_rename_function = key_rename_function

    def set_key_rename_function(self, key_rename_function):
        self._key_rename_function = key_rename_function

    def _ensure_directory_exists(self, path):
        abspath = os.path.abspath(path)
        directory = os.path.dirname(abspath)
        if not os.path.exists(directory):
            os.makedirs(directory)

    def write_to_file(self, path):
        self._ensure_directory_exists(path)

        with codecs.open(path, mode="w", encoding="utf-8") as f:
            headers = [self._key_rename_function(k) for k in self._keys]
            self._write_row(headers, f)

            for d in self._dict_iterator:
                # todo: figure out how to use csv.writer with unicode
                self._write_row([d.get(k, u"n/a") for k in self._keys], f)

    def _write_row(self, row, file_object):
        quote_escaped_row = []
        for cell in row:
            cell_string = unicode(cell)
            cell_string = re.sub(ur"\s+", u" ", cell_string)
            if u',' in cell_string:
                quote_escaped_row.append(u'"%s"' % cell_string)
            else:
                quote_escaped_row.append(cell_string)
        row_string = u",".join(quote_escaped_row)
        file_object.writelines([row_string, u"\n"])


from odk_viewer.models import DataDictionary


class DataDictionaryWriter(CsvWriter):

    def __init__(self, data_dictionary):
        self._data_dictionary = data_dictionary
        super(DataDictionaryWriter, self).__init__(
            dict_iterator=data_dictionary.get_data_for_excel(),
            keys=data_dictionary.get_keys(),
            key_rename_function=data_dictionary.get_variable_name
            )

    def get_default_file_path(self):
        this_directory = os.path.dirname(__file__)
        id_string = self._data_dictionary.id_string
        return os.path.join(this_directory, "csvs", id_string + ".csv")


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


def csv_export(request, id_string):
    dd = DataDictionary.objects.get(id_string=id_string,
                                    user=request.user)
    writer = DataDictionaryWriter(dd)
    file_path = writer.get_default_file_path()
    writer.write_to_file(file_path)
    return send_file(path=file_path, content_type="application/csv")
