from django.conf.urls.defaults import *

from django.contrib import admin
admin.autodiscover()

from controller.views import dashboard
from settings import MEDIA_ROOT

urlpatterns = patterns('',
    (r'^/?$', dashboard),

    (r'^storage/?',     include('nmis.django_eav.urls')),
    (r'^analysis/?',    include('nmis.nmis_analysis.urls')),

    (r'^dropbox/?',     include('nmis.odk_dropbox.urls')),
    (r'^submission/?',  include('nmis.odk_dropbox.urls')),
    (r'^formList/?',    include('nmis.odk_dropbox.urls')),

    (r'^admin/', include(admin.site.urls)),
    
    #No static serve in PRODUCTION
    (r'^site_media/(?P<path>.+)$', 'django.views.static.serve', {'document_root':MEDIA_ROOT}),
)
