from django.conf.urls.defaults import patterns, url
import views

SURVEY_ID = r"(?P<survey_root_name>.+)"

urlpatterns = patterns('',
    url(r"^$", views.home),
    url(r"^edit/%s/section/(?P<section_slug>\S+)/(?P<action>\S+)" % SURVEY_ID, views.edit_section),
    url(r"^edit/%s/" % SURVEY_ID, views.edit_survey),
    url(r"^delete/%s$" % SURVEY_ID, views.delete_survey),
    url(r"^download/%s\.(?P<format>json|xml)$" % SURVEY_ID, views.download_survey)
)
