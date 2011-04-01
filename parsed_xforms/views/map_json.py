import json
from bson import json_util
from django.http import HttpResponse
from common_tags import LGA_ID, DATE_TIME_START, SURVEYOR_NAME, \
    INSTANCE_DOC_NAME, ATTACHMENTS, GPS
from parsed_xforms.models import xform_instances

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
    match_lga = {LGA_ID : int(lga_id)}
    fields = [DATE_TIME_START, SURVEYOR_NAME, INSTANCE_DOC_NAME,
              LGA_ID, ATTACHMENTS, GPS]
    mongo_query = xform_instances.find(spec=match_lga, fields=fields)
    list_of_dicts = list(mongo_query)
    json_str = json.dumps(list_of_dicts, default=json_util.default)
    return HttpResponse(json_str)
