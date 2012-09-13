from django.db import models
from celery.result import AsyncResult
from django.core.files.storage import get_storage_class
from django.db.models.signals import post_delete
from odk_logger.models import XForm

XLS_EXPORT = 'xls'
CSV_EXPORT = 'csv'
KML_EXPORT = 'kml'

EXPORT_DEFS = {
    'xls': {
        'mime_type': 'vnd.ms-excel'
    },
    'xlsx': {
        'mime_type': 'vnd.openxmlformats'
    },
    'csv': {
        'mime_type': 'application/csv'
    }
}


EXPORT_TYPES = [
    (XLS_EXPORT, 'Excel'),
    (CSV_EXPORT, 'CSV'),
    #(KML_EXPORT, 'kml'),
]

EXPORT_TYPE_DICT = dict(export_type for export_type in EXPORT_TYPES)

EXPORT_PENDING = 0
EXPORT_SUCCESSFUL = 1
EXPORT_FAILED = 2


def export_delete_callback(sender, **kwargs):
    export = kwargs['instance']
    storage = get_storage_class()()
    storage.delete(export.filepath)


class Export(models.Model):
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

    def save(self, *args, **kwargs):
        if not self.pk:
            # if new, check if we've hit our limit for exports for this form,
            # if so, delete oldest
            # TODO: let user know that last export will be deleted
            num_existing_exports = Export.objects.filter(
                xform=self.xform, export_type=self.export_type).count()

            if num_existing_exports >= self.MAX_EXPORTS:
                Export._delete_oldest_export(self.xform, self.export_type)

        super(Export, self).save(*args, **kwargs)

    @classmethod
    def _delete_oldest_export(cls, xform, export_type):
        oldest_export = Export.objects.filter(
            xform=xform, export_type=export_type).order_by('created_on')[0]
        oldest_export.delete()

    @property
    def is_pending(self):
        return self.status == EXPORT_PENDING

    @property
    def is_successful(self):
        return self.status == EXPORT_SUCCESSFUL

    @property
    def status(self):
        result = AsyncResult(self.task_id)
        if self.filename:
            return EXPORT_SUCCESSFUL
        elif (result and result.ready()) or not result:
            # and not filename
            return EXPORT_FAILED
        else:
            return EXPORT_PENDING

    @property
    def filepath(self):
        if self.status == EXPORT_SUCCESSFUL:
            return "%s/%s/%s/%s/%s" % (self.xform.user.username,
                                   'exports', self.xform.id_string,
                                   self.export_type, self.filename)
        return None

post_delete.connect(export_delete_callback, sender=Export)
