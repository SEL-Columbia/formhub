from django.conf.urls.defaults import *

from django.contrib import admin
admin.autodiscover()

from settings import MEDIA_ROOT

urlpatterns = patterns('',
    url(r'^$', 'parsed_xforms.views.homepage', name='site-homepage'),

    (r'^phone_manager/', include('nmis.phone_manager.urls')),
    (r'^xform_manager/', include('nmis.xform_manager.urls')),

    (r'^admin/', include(admin.site.urls)),
    (r'^accounts/', include('registration.urls')),
    # static serve site media / only for development
    (r'^site-media/(?P<path>.+)$', 'django.views.static.serve', {'document_root' : MEDIA_ROOT}),
    (r'^xforms/', include('parsed_xforms.urls')),
    (r'^xforms/quality_reviews/', include('submission_qr.urls')),
)
