from django.db import models

class SurveyType(models.Model):
    slug = models.CharField(max_length=100)

    class Meta:
        app_label = 'odk_logger'
