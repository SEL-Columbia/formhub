from django.db import models
from odk_logger.models import XForm

XLS_EXPORT = 'xls'
CSV_EXPORT = 'csv'
KML_EXPORT = 'kml'

EXPORT_DEFS = {
    'xls' : {
        'mime_type': 'vnd.ms-excel'
    },
    'xlsx': {
        'mime_type': 'vnd.openxmlformats'
    },
    'csv': {
        'mime_type': 'application/csv'
    }
}


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
    filename = models.CharField(max_length=255, null=True, blank=True)
    export_type = models.CharField(
        max_length=10, choices=EXPORT_TYPES, default=XLS_EXPORT
    )
    task_id = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        app_label = "odk_viewer"

    # TODO: on create, limit exports to MAX_EXPORTS
