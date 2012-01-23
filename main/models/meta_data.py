from django.db import models
from odk_logger.models import XForm

def unique_type_for_form(xform, data_type):
    result = type_for_form(xform, data_type)
    if not len(result):
        result = MetaData(data_type=data_type, xform=xform)
        result.save()
        return result
    else:
        return result[0]

def type_for_form(xform, data_type):
    return MetaData.objects.filter(xform=xform, data_type=data_type)

class MetaData(models.Model):
    xform = models.ForeignKey(XForm)
    data_type = models.CharField(max_length=255)
    data_value = models.CharField(max_length=255)

    @staticmethod
    def form_license(xform):
        data_type = 'form_license'
        return unique_type_for_form(xform, data_type)

    @staticmethod
    def data_license(xform):
        data_type = 'data_license'
        return unique_type_for_form(xform, data_type)

    class Meta:
        app_label = 'main'

