from django.conf.urls.defaults import *

from django.contrib import admin
admin.autodiscover()

from settings import MEDIA_ROOT
from controller.views import dashboard

urlpatterns = patterns('',
    # odk dropbox urls
    (r'', include('nmis.odk_dropbox.urls')),

    # admin urls
    (r'^admin/', include(admin.site.urls)),
    
    # Web UI:
    # UI: Dashboard
    url(r"^/?$", dashboard),
    
    # static serve site media / only for development
    (r'^site-media/(?P<path>.+)$', 'django.views.static.serve', {'document_root' : MEDIA_ROOT}),
)
