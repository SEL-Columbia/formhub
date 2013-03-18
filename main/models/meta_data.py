import os

from django.db import models
from odk_logger.models import XForm

from hashlib import md5


def upload_to(instance, filename):
    if instance.data_type == 'media':
        return os.path.join(
            instance.xform.user.username,
            'formid-media',
            filename
        )
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
        if result.data_value is None or result.data_value == '':
            result.data_value = data_file.name
        result.data_file = data_file
        result.data_file_type = data_file.content_type
        result.save()
    return result


def type_for_form(xform, data_type):
    return MetaData.objects.filter(xform=xform, data_type=data_type)


class MetaData(models.Model):

    CROWDFORM_USERS = 'crowdform_users'

    xform = models.ForeignKey(XForm)
    data_type = models.CharField(max_length=255)
    data_value = models.CharField(max_length=255)
    data_file = models.FileField(upload_to=upload_to, null=True)
    data_file_type = models.CharField(max_length=255, null=True)

    @property
    def hash(self):
        if self.data_file.storage.exists(self.data_file.name):
            return u'%s' % md5(self.data_file.read()).hexdigest()
        return u''

    @staticmethod
    def public_link(xform, data_value=None):
        data_type = 'public_link'
        if data_value is False:
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
    def crowdform_users(xform, data_value=None):
        data_type = MetaData.CROWDFORM_USERS
        if data_value:
            doc, created = MetaData.objects.get_or_create(
                data_type=data_type,
                xform=xform,
                data_value=data_value)
            doc.save()
        return type_for_form(xform, data_type)

    @staticmethod
    def media_upload(xform, data_file=None):
        data_type = 'media'
        if data_file:
            if data_file.content_type in ['image/jpeg', 'image/png',
                                          'audio/mpeg', 'video/3gpp',
                                          'audio/wav',
                                          'audio/x-m4a', 'audio/mp3']:
                media = MetaData(data_type=data_type, xform=xform,
                                 data_value=data_file.name,
                                 data_file=data_file,
                                 data_file_type=data_file.content_type)
                media.save()
        return type_for_form(xform, data_type)

    @staticmethod
    def mapbox_layer_upload(xform, data=None):
        data_type = 'mapbox_layer'
        if data and not MetaData.objects.filter(xform=xform,
                                                data_type='mapbox_layer'):
            s = ''
            for key in data:
                s = s + data[key] + '||'
            mapbox_layer = MetaData(data_type=data_type, xform=xform,
                                    data_value=s)
            mapbox_layer.save()
        if type_for_form(xform, data_type):
            values = type_for_form(xform, data_type)[0].data_value.split('||')
            data_values = {}
            data_values['map_name'] = values[0]
            data_values['link'] = values[1]
            data_values['attribution'] = values[2]
            data_values['id'] = type_for_form(xform, data_type)[0].id
            return data_values
        else:
            return None

    class Meta:
        app_label = 'main'
