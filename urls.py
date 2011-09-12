from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from main import views as main_views

from survey_photos.views import photo_redirect

urlpatterns = patterns('',
    url(r'^$', main_views.dashboard),

    url(r'^xform_manager/', include('nmis.xform_manager.urls')),
    url(r'^xls2xform/', include('nmis.xls2xform.urls')),
    url(r'^parsed_xforms/', include('nmis.parsed_xforms.urls')),

    url(r'^survey_photos/(?P<size>\S+)/(?P<photo_id>\S+)$', photo_redirect),

    url(r'^accounts/', include('registration.backends.default.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
)
