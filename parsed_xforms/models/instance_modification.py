from xform_manager.models import Instance
from django.contrib.auth.models import User
from django.db import models


class InstanceModification(models.Model):
    user = models.ForeignKey(User, null=True)

    action = models.CharField(max_length=50)

    instance = models.ForeignKey(Instance, null=False, related_name="modifications")
    xpath = models.CharField(max_length=50)

    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "parsed_xforms"

    def process_doc(self, doc):
        if self.action=="delete":
            doc.pop(self.xpath)
        return doc