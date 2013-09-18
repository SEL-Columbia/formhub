"""
validations.py --> Defines user-written validation routines for various ODK X-forms.   (works kind of like urls.py)

This file must define a variable named "validation_patterns",
which is the value returned from a call to submission_time_validation.val_patterns(),
which takes as arguments a sequence of 2-tuples,
each of which is the return from the function submission_time_validation.val(),
which takes two arguments:
1: a Python regular expression matching the name of the X-form to be validated
2: a Python callable (i.e. function) which is used to validate one row of data from said form.
- - - - - -
said function will be called with an argument list like the following:
def dummy_callable(form_name, xml_root, request, username, uuid):
    print('form_name="%s" username="%s" uuid="%s"' % (form_name, username, uuid))
    for element in xml_root:
        print(element.tag,'=', element.text)  # each field in the X-form will appear here
    return True
--> return True to continue normal processing,
 or return False to abort record loading silently (perhaps the validation will have saved the record itself)
 or return an utils.logger_tools.OpenRosaResponseNotAcceptable Exception to abort record loading with a message
"""
from utils.submission_time_validation import val_patterns, val, dummy_callable

# validation_patterns = []  ## uncomment if extended validations are not used.

validation_patterns = val_patterns(
    val('tutorial+', dummy_callable)
)
