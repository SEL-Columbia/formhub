import os
import time
from celery import task
from datetime import datetime
from tempfile import NamedTemporaryFile
from django.core.files.base import File
from django.core.files.storage import get_storage_class
from odk_logger.models import XForm
from odk_viewer.pandas_mongo_bridge import XLSDataFrameBuilder,\
    NoRecordsFoundError
from odk_viewer.models import Export
from odk_viewer.models.export import XLS_EXPORT, CSV_EXPORT, KML_EXPORT


@task()
def create_xls_export(username, id_string, query=None, xlsx=False,
                      export_id=-1):
    # we re-query the db instead of passing model objects according to
    # http://docs.celeryproject.org/en/latest/userguide/tasks.html#state
    xform = XForm.objects.get(user__username=username, id_string=id_string)
    xls_df_builder = XLSDataFrameBuilder(username, id_string, query)
    ext = 'xls' if not xlsx else 'xlsx'
    if xls_df_builder.exceeds_xls_limits:
        ext = 'xlsx'
    temp_file = NamedTemporaryFile(suffix=("." + ext))
    # working, though export is not availale when for has 0 submissions, we
    # catch this since it potentially stops celery
    try:
        xls_df_builder.export_to(temp_file.name)
    except NoRecordsFoundError:
        pass
    basename = "%s_%s.%s" % (id_string,
                             datetime.now().strftime("%Y_%m_%d_%H_%M_%S"), ext)
    file_path = os.path.join(
        username,
        'exports',
        id_string,
        'xls',
        basename)
    # TODO: if s3 storage, make private - how will we protect local storage??
    storage = get_storage_class()()
    # seek to the beginning as required by storage classes
    temp_file.seek(0)
    export_filename = storage.save(
        file_path,
        File(temp_file, file_path))
    temp_file.close()
    export, is_new = Export.objects.get_or_create(id=export_id)
    if is_new:
        export.xform = xform
        export.export_type = XLS_EXPORT
    # always set the filename
    dir_name, basename = os.path.split(export_filename)
    export.filename = basename
    export.save()
    return export