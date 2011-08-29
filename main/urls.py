from django.conf.urls.defaults import patterns, url
from xls2xform.urls import SURVEY_ID
import views

urlpatterns = patterns('',
    url(r"^publish/%s/" % SURVEY_ID, views.publish),
)
