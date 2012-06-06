import os

from django.core.files.storage import get_storage_class
from django.db import models

from instance import Instance
from utils.image_tools import get_dimensions, resize


def upload_to(instance, filename):
    return os.path.join(
        instance.instance.user.username,
        'attachments',
        os.path.split(filename)[1])


class Attachment(models.Model):
    instance = models.ForeignKey(Instance, related_name="attachments")
    media_file = models.FileField(upload_to=upload_to)

    class Meta:
        app_label = 'odk_logger'
