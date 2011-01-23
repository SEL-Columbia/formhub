from treebeard.mp_tree import MP_Node
import math
from django.db import models
from django.conf import settings

class District(MP_Node):
    name = models.CharField(max_length=50)
    node_order_by = ['name']
    nickname = models.CharField(max_length=50)
    kml_present = models.BooleanField()
    active = models.BooleanField()
    latlng_string = models.CharField(max_length=50)

    class Meta: 
        app_label = 'odk_dropbox'
    
    def ll_diff(self, gps):
        ll = self.latlng()
        lat_delta = ll['lat'] - gps.latitude
        lng_delta = ll['lng'] - gps.longitude
        return float(math.fabs(lat_delta) + math.fabs(lng_delta))
    
    def latlng(self):
        try:
            lat, lng = self.latlng_string.split(",")
            o = {'lat': float(lat), 'lng': float(lng) }
        except:
            o = None
        
        return o
        
    def kml_uri(self):
        if not self.kml_present:
            return None
        else:
            return "%skml/%d.kml" % (settings.MEDIA_URL, self.id)
    
    def to_dict(self):
        return {'name':self.name, 'state':self.get_parent().name, \
                'coords':self.latlng_string, 'kml':self.kml_uri(), \
                'id':self.id }
