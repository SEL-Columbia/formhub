from common_tags import LGA_ID, START_TIME, SURVEYOR_NAME, \
    INSTANCE_DOC_NAME, ATTACHMENTS, GPS, SURVEY_TYPE
from parsed_xforms.models import xform_instances
from utils import json_response
from deny_if_unauthorized import deny_if_unauthorized


@deny_if_unauthorized()
def map_data_points(request, lga_id):
    """
    The map list needs these attributes for each survey to display
    the map & dropdown filters.

    * Mongo doc ID, this is the same as xform_manager.models.Instance.id
    * Date
    * Surveyor name
    * Survey Type
    * LGA ID
    * a URL to access the picture
    * GPS coordinates
    """
    match_lga = {LGA_ID: int(lga_id), GPS: {"$regex": "[0-9 .]+"}}
    fields = [START_TIME, SURVEYOR_NAME, INSTANCE_DOC_NAME,
              LGA_ID, ATTACHMENTS, GPS, SURVEY_TYPE]
    mongo_query = xform_instances.find(spec=match_lga, fields=fields)
    list_of_dicts = list(mongo_query)
    return json_response(list_of_dicts)
