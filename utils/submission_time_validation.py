import xml.etree.ElementTree as etree
import re

from django.core.exceptions import ImproperlyConfigured,  ViewDoesNotExist
from django.utils.importlib import import_module
from django.utils import six
from django.core.urlresolvers import get_callable

from utils.logger_tools import OpenRosaResponseNotAcceptable, OpenRosaResponseBadRequest

def dummy_callable(form_name, xml_root, request, username, uuid):
    print 'form_name="%s" username="%s" uuid="%s"' % (form_name, username, uuid)
    for element in xml_root:
        print element.tag,'="%s"' % (element.text,) ###
    return True

def val(regex, function):
    compiled_re = re.compile(regex)
    return (compiled_re, dummy_callable)

def val_patterns(*args):
    pattern_list = []
    for t in args:
        if isinstance(t, (list, tuple)):
            t = val(*t)
        pattern_list.append(t)
    return pattern_list

# NOTE: this import must be after the definitions of val and val_patterns
from odk_logger import validations  # sets the value of validations.validation_patterns

class Submission_Time_Validations(object):
    """  Build a Submission_Time_Validation table -- as a class attribute so that it is only created once. """
    def __new__(cls):
        stv = object.__new__(cls)
        stv.dispatch = []
        for t in validations.validation_patterns:
            if isinstance(t, (tuple, list)) and len(t) == 2:
                try:
                    compiled_regex = re.compile(t[0])
                except re.error as e:
                    raise ImproperlyConfigured(
                        '"%s" is not a valid regular expression: %s' %
                        (t[0], six.text_type(e)))
                try:
                    funct = get_callable(t[1])
                except ViewDoesNotExist:
                    raise ImproperlyConfigured(
                        'Bad Submission Time Validation: Could not import: %s' % (t[1]))
                stv.dispatch.append((compiled_regex, funct))
            else:
                raise ImproperlyConfigured(
                    'Bad Submission Time Validation: "%s" must be a two-tuple or list' % repr(t))
            return stv

    def handler(self, username, xml_file, uuid, request):
        print 'two', repr(self.dispatch) ###
        try:  # (we really need to do our own error processing and not depend on our caller)
            dummy = username
            tree = etree.parse(xml_file)
            root = tree.getroot()
            form_name = root.tag
            if form_name:

                retval = self.dispatch[0][1](form_name, root, request, username, uuid)
        except:
            retval = OpenRosaResponseBadRequest(u'Mailformed xml received')
            raise  # send any unhandled exceptions to our parent caller
        finally:
            xml_file.seek(0)    # reset the file for the next caller

        if retval is True:
            return OpenRosaResponseNotAcceptable(u'this is only a test')###
        return retval  # if "None", all is well -- continue processing this record
