from django.db import models
from .instance import Instance

class Attachment(models.Model):
    instance = models.ForeignKey(Instance, related_name="attachments")
    media_file = models.FileField(upload_to="attachments")

    class Meta:
        app_label = 'xform_manager'
