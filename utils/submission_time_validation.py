import xml.etree.ElementTree as etree
import re

from django.core.exceptions import ImproperlyConfigured,  ViewDoesNotExist
from django.utils.importlib import import_module
from django.utils import six
from django.core.urlresolvers import get_callable

from utils.logger_tools import OpenRosaResponseNotAcceptable, OpenRosaResponseBadRequest

def dummy_callable(form_name, xml_root, request, username, uuid):
    """
    callback functions for validations.py should have this footprint
    @param form_name: .xml filename of the X-form (ODK form)
    @param xml_root:  see the Python manual for xml.etree.ElementTree
    @param request:  the html request from the django view
    @param username:  the django session user
    @param uuid:
    @return:  True=continue normally, False=do not store this record in formhub, Exception=make user fix record
    """
    print 'form_name="%s" username="%s" uuid="%s"' % (form_name, username, uuid)
    kids = False
    for element in xml_root:
        print '%s="%s"' % (element.tag, element.text)
        if element.tag == 'has_children' and element.text == "1":
            kids = True
    if kids:
        return OpenRosaResponseNotAcceptable('No children are permitted in this example!')
    return form_name.endswith('-test')  # test forms are swallowed silently

class ValidationNode(object):
    def __init__(self, regex, function):
        try:
            self.regex = re.compile(regex)
        except re.error as e:
            raise ImproperlyConfigured(
                '"%s" is not a valid regular expression: %s' %
                (regex, six.text_type(e)))
        try:
            self.callback = get_callable(function)
        except ViewDoesNotExist:
            raise ImproperlyConfigured(
                'Bad Submission Time Validation: Could not import: %s' % function)

def val(regex, function):
    return ValidationNode(regex, function)

def val_patterns(*args):
    pattern_list = []
    for t in args:
        if not isinstance(t, ValidationNode):
            t = val(*t)
        pattern_list.append(t)
    return pattern_list


# NOTE: this import must be after the definitions of val and val_patterns
from odk_logger import validations  # sets the value of validations.validation_patterns

class Submission_Time_Validations(object):
    """  Build a Submission_Time_Validation table -- as a class attribute so that it is only created once. """

    def __new__(cls):
        stv = object.__new__(cls)
        stv.dispatch = validations.validation_patterns
        return stv

    def handler(self, username, xml_file, uuid, request):
        print 'two', repr(self.dispatch) ###
        try:  # (we really need to do our own error processing and not depend on our caller)
            tree = etree.parse(xml_file)
            root = tree.getroot()
            form_name = root.tag
        except:
            retval = OpenRosaResponseBadRequest(u'Malformed xml received')
        else:
            for valdtr in self.dispatch:  # see if this form has validation defined
                match = valdtr.regex.match(form_name)
                if match:
                    retval = valdtr.callback(form_name, root, request, username, uuid)
                    break
        finally:
            xml_file.seek(0)    # reset the file for the next caller

        return retval  # --> return True to continue normal processing,
        # or return False to abort record loading silently (perhaps the validation will have saved the record itself)
        # or return an utils.logger_tools.OpenRosaResponseNotAcceptable Exception to abort record loading with a message

