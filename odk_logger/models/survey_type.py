from django.db import models


class SurveyType(models.Model):
    slug = models.CharField(max_length=100, unique=True)

    class Meta:
        app_label = 'odk_logger'

    def __unicode__(self):
        return "SurveyType: %s" % self.slug
