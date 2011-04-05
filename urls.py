from django.conf.urls.defaults import *

from django.contrib import admin
admin.autodiscover()

from settings import MEDIA_ROOT
from xform_manager import views as xform_manager_views
OPT_GROUP_REGEX = "((?P<group_name>[^/]+)/)?"

urlpatterns = patterns('',
    url(r'^$', 'parsed_xforms.views.homepage', name='site-homepage'),

    (r'^phone_manager/', include('nmis.phone_manager.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^accounts/', include('registration.urls')),
    # static serve site media / only for development
    (r'^site-media/(?P<path>.+)$', 'django.views.static.serve', {'document_root' : MEDIA_ROOT}),
    (r'^xforms/quality_reviews/', include('submission_qr.urls')),

    #including direct link to urls for odk access.
    url(r"^%sformList$" % OPT_GROUP_REGEX, xform_manager_views.formList),
    url(r"^%ssubmission$" % OPT_GROUP_REGEX, xform_manager_views.submission),
    (r'^xform_manager/', include('nmis.xform_manager.urls')),
    (r'^sentry/', include('sentry.urls')),
    (r'^xforms/', include('parsed_xforms.urls')),
    (r'^$', include('parsed_xforms.urls')),
)
