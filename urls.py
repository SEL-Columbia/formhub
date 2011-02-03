from django.conf.urls.defaults import *

from django.contrib import admin
admin.autodiscover()

from settings import MEDIA_ROOT

urlpatterns = patterns('',
    (r'^', include('nmis.odk_dropbox.urls')),
    (r'^phone_manager/', include('nmis.phone_manager.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^accounts/', include('registration.urls')),
    # static serve site media / only for development
    (r'^site-media/(?P<path>.+)$', 'django.views.static.serve', {'document_root' : MEDIA_ROOT}),
)
