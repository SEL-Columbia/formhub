# WE SHOULD PUT MORE STRUCTURE ON THESE TAGS SO WE CAN ACCESS DOCUMENT
# FIELDS ELEGANTLY

# These are common variable tags that we'll want to access
ID_STRING = u"_id_string"
INSTANCE_DOC_NAME = u"_name"
ID = u"_id"
DATE_TIME_START = u"start"
DATE_TIME_END = u"end"
IMEI = u"device_id"
PICTURE = u"picture"
GPS = u"location/gps"
LGA = u"lga"

# value of INSTANCE_DOC_NAME that indicates a regisration form
REGISTRATION = u"registration"
# keys that we'll look for in the registration form
REGISTRATION_NAME = u"name"

# extra fields that we're adding to our mongo doc
SURVEYOR_NAME = u"_surveyor_name"
DISTRICT_ID = u"_district_id"
ATTACHMENTS = u"_attachments"
DATE = u"_date"

PHONE_UPDATE = u"phone"
