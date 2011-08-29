from django.conf.urls.defaults import patterns, url
import views

SURVEY_ID = r"(?P<survey_id>.+)"

urlpatterns = patterns('',
    url(r"^$", views.home),
    url(r"^edit/%s/section/(?P<section_slug>\S+)/(?P<action>\S+)" % SURVEY_ID, views.edit_section),
    url(r"^edit/%s/" % SURVEY_ID, views.edit_xform),
    url(r"^delete/%s$" % SURVEY_ID, views.delete_xform),
    url(r"^download/%s\.(?P<format>json|xml)$" % SURVEY_ID, views.download_xform)
)
