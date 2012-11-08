import os
from django.db import models
from celery.result import AsyncResult
from django.core.files.storage import get_storage_class
from django.db.models.signals import post_delete
from odk_logger.models import XForm
from django.utils.translation import ugettext_lazy, ugettext as _


def export_delete_callback(sender, **kwargs):
    export = kwargs['instance']
    storage = get_storage_class()()
    storage.delete(export.filepath)


class Export(models.Model):
    class ExportTypeError(Exception):
        def __unicode__(self):
            return _(u"Invalid export type specified")
        def __str__(self):
            return unicode(self).encode('utf-8')

    XLS_EXPORT = 'xls'
    CSV_EXPORT = 'csv'
    KML_EXPORT = 'kml'

    EXPORT_MIMES = {
        'xls': 'vnd.ms-excel',
        'xlsx': 'vnd.openxmlformats',
        'csv': 'application/csv'
    }

    EXPORT_TYPES = [
        (XLS_EXPORT, 'Excel'),
        (CSV_EXPORT, 'CSV'),
        #(KML_EXPORT, 'kml'),
    ]

    EXPORT_TYPE_DICT = dict(export_type for export_type in EXPORT_TYPES)

    PENDING = 0
    SUCCESSFUL = 1
    FAILED = 2

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
    # time of last submission when this export was created
    time_of_last_submission = models.DateTimeField(null=True, default=None)

    class Meta:
        app_label = "odk_viewer"
        unique_together = (("xform", "filename"),)

    def save(self, *args, **kwargs):
        if not self.pk and self.xform:
            # if new, check if we've hit our limit for exports for this form,
            # if so, delete oldest
            # TODO: let user know that last export will be deleted
            num_existing_exports = Export.objects.filter(
                xform=self.xform, export_type=self.export_type).count()

            if num_existing_exports >= self.MAX_EXPORTS:
                Export._delete_oldest_export(self.xform, self.export_type)

            # update time_of_last_submission with xform.time_of_last_submission
            self.time_of_last_submission = self.xform.time_of_last_submission()
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
        return self.status == Export.PENDING

    @property
    def is_successful(self):
        return self.status == Export.SUCCESSFUL

    @property
    def status(self):
        result = AsyncResult(self.task_id)
        if self.filename:
            return Export.SUCCESSFUL
        elif (result and result.ready()) or not result:
            # and not filename
            return Export.FAILED
        else:
            return Export.PENDING

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

    @classmethod
    def exports_outdated(cls, xform, export_type):
        # get newest export for xform
        qs = Export.objects.filter(xform=xform, export_type=export_type)\
             .order_by('-created_on')[:1]
        if qs.count() > 0 and qs[0].time_of_last_submission is not None \
                and xform.time_of_last_submission() is not None:
            export = qs[0]
            # get last submission date stored in export
            last_submission_time_at_export = export.time_of_last_submission
            return last_submission_time_at_export < \
                   xform.time_of_last_submission()
        # return true if we can't determine the status, to force auto-generation
        return True

    @classmethod
    def is_filename_unique(cls, xform, filename):
        return Export.objects.filter(xform=xform,
            filename=filename).count() == 0

post_delete.connect(export_delete_callback, sender=Export)
