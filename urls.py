from django.conf.urls.defaults import *

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^storage/?',     include('nmis.django_eav.urls')),
    (r'^analysis/?',    include('nmis.nmis_analysis.urls')),

    (r'^dropbox/?',     include('nmis.odk_dropbox.urls')),
    (r'^submission/?',  include('nmis.odk_dropbox.urls')),
    (r'^formList/?',    include('nmis.odk_dropbox.urls')),

    (r'^admin/', include(admin.site.urls)),
)
