import sys
from StringIO import StringIO
from celery import task
from django.db import transaction
from django.core.mail import mail_admins
from odk_viewer.models import Export
from utils.export_tools import generate_export
from utils.logger_tools import mongo_sync_status
from pandas_mongo_bridge import NoRecordsFoundError


def create_async_export(xform, export_type, query, force_xlsx):
    username = xform.user.username
    id_string = xform.id_string

    @transaction.commit_on_success
    def _create_export(xform, export_type):
        return Export.objects.create(xform=xform, export_type=export_type)

    export = _create_export(xform, export_type)
    result = None
    if export_type == Export.XLS_EXPORT:
        # start async export
        result = create_xls_export.apply_async(
            (), {
                'username': username,
                'id_string': id_string,
                'export_id': export.id,
                'query': query,
                'force_xlsx': force_xlsx
            }, countdown=10)
    elif export_type == Export.CSV_EXPORT:
        # start async export
        result = create_csv_export.apply_async(
            (), {
                'username': username,
                'id_string': id_string,
                'export_id': export.id,
                'query': query
            }, countdown=10)
    else:
        raise Export.ExportTypeError
    if result:
        export.task_id = result.task_id
        export.save()
        return export, result
    return None


@task()
def create_xls_export(username, id_string, export_id, query=None,
                      force_xlsx=False):
    # we re-query the db instead of passing model objects according to
    # http://docs.celeryproject.org/en/latest/userguide/tasks.html#state
    ext = 'xls' if not force_xlsx else 'xlsx'

    export = Export.objects.get(id=export_id)
    # though export is not available when for has 0 submissions, we
    # catch this since it potentially stops celery
    try:
        gen_export = generate_export(Export.XLS_EXPORT, ext, username, id_string,
                                 export_id, query)
    except (Exception, NoRecordsFoundError) as e:
        export.internal_status = Export.FAILED
        export.save()
        # raise for now to let celery know we failed - doesnt seem to break celery
        raise
    else:
        return gen_export.id

@task()
def create_csv_export(username, id_string, export_id, query=None):
    # we re-query the db instead of passing model objects according to
    # http://docs.celeryproject.org/en/latest/userguide/tasks.html#state

    export = Export.objects.get(id=export_id)
    try:
        # though export is not available when for has 0 submissions, we
        # catch this since it potentially stops celery
        gen_export = generate_export(Export.CSV_EXPORT, 'csv', username, id_string,
                                 export_id, query)
    except (Exception, NoRecordsFoundError) as e:
        export.internal_status = Export.FAILED
        export.save()
    else:
        return gen_export.id

@task()
def email_mongo_sync_status():
    # run function to check status
    report_string = mongo_sync_status()
    report_string += "\nTo re-sync, ssh into the server and run\n\n" \
                   "python manage.py sync_mongo -r [username] [id_string]\n\n" \
                   "To force complete delete and re-creationuse the -a option" \
                   " \n\n" \
                   "python manage.py sync_mongo -ra [username] [id_string]\n"
    # send email
    mail_admins("Mongo DB sync status", report_string)