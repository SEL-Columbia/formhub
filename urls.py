from django.conf.urls.defaults import patterns, include, url
from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    # django default stuff
    url(r'^accounts/', include('main.registration_urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # main website views
    url(r'^$', 'main.views.home'),
    url(r'^tutorial/$', 'main.views.tutorial'),
    url(r'^syntax/$', 'main.views.syntax'),
    url(r'^forms/$', 'main.views.form_gallery'),
    url(r'^forms/(?P<uuid>[^/]+)$', 'main.views.show'),
    url(r'^people/$', 'main.views.members_list'),
    url(r'^xls2xform/$', 'main.views.xls2xform'),
    url(r'^support/$', 'main.views.support'),
    url(r'^stats/$', 'staff.views.stats'),
    url(r'^login_redirect/$', 'main.views.login_redirect'),
    url(r'^(?P<username>[^/]+)/$', 'main.views.profile'),
    url(r'^(?P<username>[^/]+)/profile$', 'main.views.public_profile'),
    url(r'^(?P<username>[^/]+)/settings', 'main.views.profile_settings'),
    url(r'^(?P<username>[^/]+)/cloneform$', 'main.views.clone_xlsform'),

    # form specific
    url(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)$', 'main.views.show'),
    url(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/edit$', 'main.views.edit'),
    url(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/perms$', 'main.views.set_perm'),
    url(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/photos', 'main.views.form_photos'),
    url(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/doc/(?P<data_id>[^/]+)', 'main.views.download_metadata'),
    url(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/submission/(?P<uuid>[^/]+)$', 'main.views.show_submission'),

    # stats
    url(r"^stats/submissions/$", 'staff.views.submissions'),

    # exporting stuff
    url(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/data\.csv$", 'odk_viewer.views.csv_export'),
    url(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/data\.xls$", 'odk_viewer.views.xls_export'),
    url(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/data\.kml$", 'odk_viewer.views.kml_export'),
    url(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/data\.zip", 'odk_viewer.views.zip_export'),
    url(r"^odk_viewer/survey/(?P<instance_id>\d+)/$", 'odk_viewer.views.survey_responses'),
    url(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/map", 'odk_viewer.views.map_view'),
    url(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/enter-data", 'odk_logger.views.enter_data'),

    # odk data urls
    url(r"^submission$", 'odk_logger.views.submission'),
    url(r"^(?P<username>\w+)/formList$", 'odk_logger.views.formList'),
    url(r"^(?P<username>\w+)/submission$", 'odk_logger.views.submission'),
    url(r"^(?P<username>\w+)/bulk-submission$", 'odk_logger.views.bulksubmission'),
    url(r"^(?P<username>\w+)/bulk-submission-form$", 'odk_logger.views.bulksubmission_form'),
    url(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/form\.xml$", 'odk_logger.views.download_xform', name="download_xform"),
    url(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/form\.xls$", 'odk_logger.views.download_xlsform', name="download_xlsform"),
    url(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/form\.json", 'odk_logger.views.download_jsonform', name="download_jsonform"),
    url(r"^(?P<username>\w+)/delete/(?P<id_string>[^/]+)/$", 'odk_logger.views.delete_xform'),
    url(r"^(?P<username>\w+)/(?P<id_string>[^/]+)/toggle_downloadable/$", 'odk_logger.views.toggle_downloadable'),

    # static media
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT}),
)

