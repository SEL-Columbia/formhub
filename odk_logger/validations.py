"""
validations.py --> Defines Submission-time Validation routines for various ODK X-forms.   (works kind of like urls.py)

This file must define a variable named "validation_patterns",
which is the value returned from a call to submission_time_validation.val_patterns(),
which takes as arguments a sequence of 2-tuples,
each of which is the return from the function submission_time_validation.val(),
which takes two arguments:
1: a Python regular expression matching the name of the X-form to be validated
2: a Python callable (i.e. function) which is used to validate one row of data from said form.
- - - - - -
said function will be called with an argument list like the following:
def dummy_callable(form_name, xml_root, request, username, uuid, media_files):
    for element in xml_root:
        pass  # each field in the X-form will appear here
    return False
--> return False to continue normal processing,
 or return True to inhibit record loading with a success indication
 or return an utils.logger_tools.OpenRosaResponseNotAcceptable Exception to inhibit record loading with a message
"""
from utils.submissionTime_validation import val_patterns, val, dummy_callable

# validation_patterns = []  ## if extended validations are not used, set this to an empty list

validation_patterns = val_patterns(
    val('s+_t+_validation_x+', dummy_callable)
)
