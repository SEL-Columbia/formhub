from django.conf.locale import sv
from django.db import models
from odk_logger.models.xform import XForm
from restservice import SERVICE_CHOICES


class RestService(models.Model):

    class Meta:
        app_label = 'restservice'
        unique_together = ('service_url', 'xform', 'name')

    service_url = models.URLField("Service URL", verify_exists=False)
    xform = models.ForeignKey(XForm)
    name = models.CharField(max_length=50, choices=SERVICE_CHOICES)

    def get_service_definition(self):
        m = __import__(''.join(['restservice.services.', self.name]),\
            globals(),locals(), ['ServiceDefinition'])
        return m.ServiceDefinition