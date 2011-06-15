from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from xform_manager import views as xform_manager_views
OPT_GROUP_REGEX = "((?P<group_name>[^/]+)/)?"

from main.views import baseline_redirect

urlpatterns = patterns('',
    url(r"^%sformList$" % OPT_GROUP_REGEX, xform_manager_views.formList),
    url(r"^%ssubmission$" % OPT_GROUP_REGEX, xform_manager_views.submission),
    url(r'^xform_manager/', include('nmis.xform_manager.urls')),
    url(r'^accounts/', include('registration.urls')),
    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    
    url(r'^baseline/', include('parsed_xforms.urls')),
    url(r'^xforms/', include('parsed_xforms.urls')),
    url(r'^$', baseline_redirect),
)
