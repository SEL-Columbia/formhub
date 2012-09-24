import os
from datetime import datetime
from django.core.files.base import File
from django.core.files.temp import NamedTemporaryFile
from django.db import models
from celery.result import AsyncResult
from django.core.files.storage import get_storage_class
from django.db.models.signals import post_delete
from odk_logger.models import XForm
from odk_viewer.pandas_mongo_bridge import XLSDataFrameBuilder, CSVDataFrameBuilder

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


def _df_builder_for_export_type(export_type, username, id_string, filter_query=None):
    if export_type == XLS_EXPORT:
        return XLSDataFrameBuilder(username, id_string, filter_query)
    elif export_type == CSV_EXPORT:
        return CSVDataFrameBuilder(username, id_string, filter_query)
    else:
        raise ValueError


def generate_export(export_type, extension, username, id_string, export_id = None, filter_query=None):
    """
    Create appropriate export object given the export type
    """
    xform = XForm.objects.get(user__username=username, id_string=id_string)
    df_builder = _df_builder_for_export_type(export_type, username, id_string, filter_query)
    if hasattr(df_builder, 'get_exceeds_xls_limits') and df_builder.get_exceeds_xls_limits():
        extension = 'xlsx'

    temp_file = NamedTemporaryFile(suffix=("." + extension))
    df_builder.export_to(temp_file.name)
    basename = "%s_%s.%s" % (id_string,
                             datetime.now().strftime("%Y_%m_%d_%H_%M_%S"), extension)
    file_path = os.path.join(
        username,
        'exports',
        id_string,
        export_type,
        basename)

    # TODO: if s3 storage, make private - how will we protect local storage??
    storage = get_storage_class()()
    # seek to the beginning as required by storage classes
    temp_file.seek(0)
    export_filename = storage.save(
        file_path,
        File(temp_file, file_path))
    temp_file.close()
    # create export object
    export, is_new = Export.objects.get_or_create(id=export_id, xform=xform, export_type=export_type)
    dir_name, basename = os.path.split(export_filename)
    export.filename = basename
    export.save()
    return export


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
    # need to save an the filedir since when an xform is deleted, it cascades its exports which then try to
    # delete their files and try to access the deleted xform - bad things happen
    filedir = models.CharField(max_length=255, null=True, blank=True)
    export_type = models.CharField(
        max_length=10, choices=EXPORT_TYPES, default=XLS_EXPORT
    )
    task_id = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        app_label = "odk_viewer"

    def save(self, *args, **kwargs):
        if not self.pk and self.xform:
            # if new, check if we've hit our limit for exports for this form,
            # if so, delete oldest
            # TODO: let user know that last export will be deleted
            num_existing_exports = Export.objects.filter(
                xform=self.xform, export_type=self.export_type).count()

            if num_existing_exports >= self.MAX_EXPORTS:
                Export._delete_oldest_export(self.xform, self.export_type)
        if self.filename:
            self._update_filedir()
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

    def _update_filedir(self):
        assert(self.filename)
        self.filedir = os.path.join(self.xform.user.username,
                                    'exports', self.xform.id_string,
                                    self.export_type)
    @property
    def filepath(self):
        if self.filedir and self.filename:
            return os.path.join(self.filedir, self.filename)
        return None

post_delete.connect(export_delete_callback, sender=Export)
