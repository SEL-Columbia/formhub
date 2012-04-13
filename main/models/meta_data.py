from django.db import models
from odk_logger.models import XForm
import os

def upload_to(instance, filename):
    return os.path.join(
        instance.xform.user.username,
        'docs',
        filename
        )

def unique_type_for_form(xform, data_type, data_value=None, data_file=None):
    result = type_for_form(xform, data_type)
    if not len(result):
        result = MetaData(data_type=data_type, xform=xform)
        result.save()
    else:
        result = result[0]
    if data_value:
        result.data_value = data_value
        result.save()
    if data_file:
        if result.data_value == None or result.data_value == '':
            result.data_value = data_file.name
        result.data_file = data_file
        result.data_file_type = data_file.content_type
        result.save()
    return result

def type_for_form(xform, data_type):
    return MetaData.objects.filter(xform=xform, data_type=data_type)

def remove_type_for_form(xform, data_type):
    result = type_for_form(xform, data_type)
    if(result):
        result.delete()

class MetaData(models.Model):
    xform = models.ForeignKey(XForm)
    data_type = models.CharField(max_length=255)
    data_value = models.CharField(max_length=255)
    data_file = models.FileField(upload_to=upload_to, null=True)
    data_file_type = models.CharField(max_length=255, null=True)

    @staticmethod
    def public_link(xform, data_value=None):
        data_type = 'public_link'
        if data_value == False:
            data_value = 'False'
        metadata = unique_type_for_form(xform, data_type, data_value)
        # make text field a boolean
        if metadata.data_value == 'True':
            return True
        else:
            return False

    @staticmethod
    def form_license(xform, data_value=None):
        data_type = 'form_license'
        return unique_type_for_form(xform, data_type, data_value)

    @staticmethod
    def data_license(xform, data_value=None):
        data_type = 'data_license'
        return unique_type_for_form(xform, data_type, data_value)

    @staticmethod
    def source(xform, data_value=None, data_file=None):
        data_type = 'source'
        return unique_type_for_form(xform, data_type, data_value, data_file)

    @staticmethod
    def supporting_docs(xform, data_file=None):
        data_type = 'supporting_doc'
        if data_file:
            doc = MetaData(data_type=data_type, xform=xform,
                    data_value=data_file.name,
                    data_file=data_file,
                    data_file_type=data_file.content_type)
            doc.save()
        return type_for_form(xform, data_type)

    @staticmethod
    def enumerator_username(xform, data_value=None):
        data_type = 'enumerator_username'
        return unique_type_for_form(xform, data_type, data_value)

    @staticmethod
    def enumerator_password(xform, data_value=None):
        data_type = 'enumerator_password'
        return unique_type_for_form(xform, data_type, data_value)

    @staticmethod
    def remove_enumerator_username(xform, data_value=None):
        data_type = 'enumerator_username'
        remove_type_for_form(xform, data_type)

    @staticmethod
    def remove_enumerator_password(xform, data_value=None):
        data_type = 'enumerator_password'
        remove_type_for_form(xform, data_type)

    class Meta:
        app_label = 'main'

