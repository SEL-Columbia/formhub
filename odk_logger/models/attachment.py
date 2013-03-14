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
    mimetype = models.CharField(
        max_length=20, null=False, blank=True, default='')

    class Meta:
        app_label = 'odk_logger'

    @property
    def full_filepath(self):
        if self.media_file:
            default_storage = get_storage_class()()
            try:
                return default_storage.path(self.media_file.name)
            except NotImplementedError:
                # read file from s3
                name, ext = os.path.splitext(self.media_file.name)
                tmp = NamedTemporaryFile(suffix=ext, delete=False)
                f = default_storage.open(self.media_file.name)
                tmp.write(f.read())
                tmp.close()
                return tmp.name
        return None
