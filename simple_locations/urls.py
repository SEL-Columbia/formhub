from django.conf.urls.defaults import *
from simple_locations.views import *

urlpatterns = patterns('',
   (r'^simple_locations/edit/(?P<area_id>[0-9]+)/$', edit_location),
   (r'^simple_locations/add/((?P<parent_id>[0-9]+)/){0,1}$', add_location),
   (r'^simple_locations/delete/(?P<area_id>[0-9]+)/$', delete_location),
   (r'^simple_locations/render_tree/$', render_location),
   (r'^simple_locations/$', simple_locations),
)