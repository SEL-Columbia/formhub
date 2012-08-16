from django.db import models
from odk_logger.models import XForm

XLS_EXPORT = 'xls'
CSV_EXPORT = 'csv'
KML_EXPORT = 'kml'


def get_export_filename(instance, filename):
    pass


class Export(models.Model):
    EXPORT_TYPES = (
        (XLS_EXPORT, 'Excel'),
        (CSV_EXPORT, 'csv'),
        (KML_EXPORT, 'kml'),
    )
    # max no. of export files a user can keep
    MAX_EXPORTS = 10

    xform = models.ForeignKey(XForm)
    created_on = models.DateTimeField(auto_now=True, auto_now_add=True)
    filename = models.CharField(max_length=255)
    export_type = models.CharField(
        max_length=10, choices=EXPORT_TYPES, default=XLS_EXPORT
    )

    class Meta:
        app_label = "odk_viewer"

    # TODO: on create, limit exports to MAX_EXPORTS
