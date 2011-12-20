from django.conf.urls.defaults import patterns, include, url
from django.conf import settings


# Uncomment the next two lines to enable the admin:
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    # django default stuff
    url(r'^accounts/', include('registration.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # main website views
    url(r'^$', 'main.views.home'),
    url(r'^tutorial/$', 'main.views.tutorial'),
    url(r'^syntax/$', 'main.views.syntax'),
    url(r'^gallery/$', 'main.views.gallery'),
    url(r'^support/$', 'main.views.support'),
    url(r'^login_redirect/$', 'main.views.login_redirect'),
    url(r'^(?P<username>[^/]+)/$', 'main.views.profile'),

    # stats
    url(r"^stats/submissions/$", 'stats.views.submissions'),

    # exporting stuff
    url(r"^odk_viewer/export_spreadsheet/(?P<id_string>[^/]*)\.csv$", 'odk_viewer.views.csv_export'),
    url(r"^odk_viewer/export_spreadsheet/(?P<id_string>[^/]*)\.xls$", 'odk_viewer.views.xls_export'),
    url(r"^odk_viewer/survey/(?P<pk>\d+)/$", 'odk_viewer.views.survey_responses'),
    url(r"^odk_viewer/map/(?P<id_string>[^/]*)/$", 'odk_viewer.views.map'),

    # odk data urls
    url(r"^(?P<username>\w+)/formList$", 'odk_logger.views.formList'),
    url(r"^(?P<username>\w+)/submission$", 'odk_logger.views.submission'),
    url(r"^(?P<username>\w+)/(?P<id_string>[^/]+)\.xml$", 'odk_logger.views.download_xform', name="download_xform"),
    url(r"^(?P<username>\w+)/delete/(?P<id_string>[^/]+)/$", 'odk_logger.views.delete_xform'),
    url(r"^(?P<username>\w+)/(?P<id_string>[^/]+)/toggle_downloadable/$", 'odk_logger.views.toggle_downloadable'),

    # static media
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT}),
)
