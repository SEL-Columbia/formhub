from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from main import views as main_views

urlpatterns = patterns('',
    url(r'^$', main_views.dashboard),
    url(r'^tutorial/$', main_views.tutorial),

    url(r'^odk_viewer/', include('odk_viewer.urls')),

    url(r'^accounts/', include('registration.backends.default.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^(?P<username>[^/]+)/', include('odk_logger.urls')),
)
