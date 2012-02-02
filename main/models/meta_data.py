from django.db import models
from odk_logger.models import XForm
import os

def unique_type_for_form(xform, data_type, data_value=None):
    result = type_for_form(xform, data_type)
    if not len(result):
        result = MetaData(data_type=data_type, xform=xform)
        result.save()
    else:
        result = result[0]
    if data_value:
        result.data_value = data_value
        result.save()
    return result

def type_for_form(xform, data_type):
    return MetaData.objects.filter(xform=xform, data_type=data_type)

class MetaData(models.Model):
    xform = models.ForeignKey(XForm)
    data_type = models.CharField(max_length=255)
    data_value = models.CharField(max_length=255)
    data_file = models.FileField(upload_to="DATA_FILE", null=True)

    @staticmethod
    def form_license(xform, data_value=None):
        data_type = 'form_license'
        return unique_type_for_form(xform, data_type, data_value)

    @staticmethod
    def data_license(xform, data_value=None):
        data_type = 'data_license'
        return unique_type_for_form(xform, data_type, data_value)

    @staticmethod
    def source(xform, data_value=None):
        data_type = 'source'
        return unique_type_for_form(xform, data_type, data_value)

    class Meta:
        app_label = 'main'

