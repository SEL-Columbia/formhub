from django.db import models

class SurveyTypeMapData(models.Model):
    survey_type = models.OneToOneField('xform_manager.surveytype')
    color = models.CharField(max_length=12, default="Black")

    def to_dict(self):
        return {
            'slug': self.survey_type.slug,
            'color': self.color
        }
    
    def __unicode__(self):
        return "SurveyTypeMapData: %s" % self.survey_type.slug