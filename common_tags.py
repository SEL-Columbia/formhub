from odk_logger.xform_instance_parser import XFORM_ID_STRING

# WE SHOULD PUT MORE STRUCTURE ON THESE TAGS SO WE CAN ACCESS DOCUMENT
# FIELDS ELEGANTLY

# These are common variable tags that we'll want to access
INSTANCE_DOC_NAME = u"_name"
ID = u"_id"
UUID = u"_uuid"
PICTURE = u"picture"
GPS = u"location/gps"
LGA = u"lga"
SURVEY_TYPE = u'_survey_type_slug'

# Phone IMEI:
DEVICE_ID = u"device_id" # This tag was used in Phase I
IMEI = u"imei"           # This tag was used in Phase II
# Survey start time:
START_TIME = u"start_time" # This tag was used in Phase I
START = u"start"           # This tag was used in Phase II
END_TIME = u"end_time"
END = u"end"

# value of INSTANCE_DOC_NAME that indicates a regisration form
REGISTRATION = u"registration"
# keys that we'll look for in the registration form
NAME = u"name"

# extra fields that we're adding to our mongo doc
ATTACHMENTS = u"_attachments"
DATE = u"_date"
