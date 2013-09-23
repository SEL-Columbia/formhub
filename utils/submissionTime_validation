import xml.etree.ElementTree as etree
import re

from django.core.exceptions import ImproperlyConfigured,  ViewDoesNotExist
from django.utils.importlib import import_module
from django.utils import six
from django.core.urlresolvers import get_callable

from utils.logger_tools import OpenRosaResponseNotAcceptable, OpenRosaResponseBadRequest

def dummy_callable(form_name, xml_root, request, username, uuid, media_files):
    """
    callback functions for validations.py should have this footprint
    @param form_name: .xml filename of the X-form (ODK form)
    @param xml_root:  see the Python manual for xml.etree.ElementTree
    @param request:  the html request from the django view
    @param username:  the django session user
    @param uuid:
    @param media_files:
    @return:  False=continue normally, True=inhibit storage of this record in formhub, Exception=make user fix record
    """
    print 'form_name="%s" username="%s" uuid="%s"' % (form_name, username, uuid)
    reject = False
    inhibit = False
    for element in xml_root:
        print '%s="%s"' % (element.tag, element.text)
        if element.tag == 'reject_this' and element.text == "1":
            reject = True
        if element.tag == 'inhibit_this' and element.text == "1":
            inhibit = True
    if reject:
        return OpenRosaResponseNotAcceptable('Record refused because "reject_this" was True.')
    return inhibit  # If True, the record is not stored in Mongo database

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

    def handler(self, username, xml_file, uuid, request, media_files):
        inhibit = True  # default to normal operation
        try:  # catch xml parsing errors
            tree = etree.parse(xml_file)
            root = tree.getroot()
            form_name = root.tag
        except:
            inhibit = OpenRosaResponseBadRequest('Malformed xml received')
        else:
            for valdtr in self.dispatch:  # see if this form has validation defined
                match = valdtr.regex.match(form_name)
                if match:
                    inhibit = valdtr.callback(form_name, root, request, username, uuid, media_files)
                    break
        finally:
            xml_file.seek(0)    # reset the file for the next caller

        return inhibit  # --> return True to continue normal processing,
        # or return False to abort record loading silently (perhaps the validation will have saved the record itself)
        # or return an utils.logger_tools.OpenRosaResponseNotAcceptable Exception to abort record loading with a message

