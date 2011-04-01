from common_tags import LGA_ID, DATE_TIME_START, SURVEYOR_NAME, \
    INSTANCE_DOC_NAME, ATTACHMENTS, GPS
from parsed_xforms.models import xform_instances
from utils import json_response

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
    return json_response(list_of_dicts)

from django.core.urlresolvers import reverse
from nga_districts.models import LGA
from parsed_xforms.models import ParsedInstance

def links_to_json_for_lga_maps(request):
    result = u""
    for lga in LGA.get_ordered_phase2_query_set():
        d = {u"count" : ParsedInstance.objects.filter(lga=lga).count(),
             u"url" : reverse(map_data_points, kwargs={'lga_id' : lga.id}),
             u"name" : lga.name,}
        result += u'%(count)s: <a href="%(url)s">%(name)s</a> <br/>' % d
    return HttpResponse(result)
