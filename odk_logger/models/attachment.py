from django.db import models
from .instance import Instance
import os
from django.core.files.storage import get_storage_class
from utils.logger_tools import get_dimensions, resize

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

    def save(self, *args, **kwargs):
        """
        Save Photo after ensuring it is not blank.  Resize as needed.
        """

        if not self.id and not self.media_file:
            return

        super(Attachment, self).save()

        resize(self.media_file.name)
