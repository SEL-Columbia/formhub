from django.db import models
from .instance import Instance

class Attachment(models.Model):
    instance = models.ForeignKey(Instance, related_name="attachments")
    attachment = models.FileField(upload_to="attachments")

    class Meta:
        app_label = 'odk_dropbox'
