from celery import task
from odk_viewer.models import Export
from utils.export_tools import generate_export


def create_async_export(xform, export_type, query, force_xlsx):
    username = xform.user.username
    id_string = xform.id_string
    export = Export.objects.create(xform=xform, export_type=export_type)
    result = None
    if export_type == Export.XLS_EXPORT:
        # start async export
        result = create_xls_export.apply_async(
            (), {
                'username': username,
                'id_string': id_string,
                'query': query,
                'force_xlsx': force_xlsx,
                'export_id': export.id
            })
    elif export_type == Export.CSV_EXPORT:
        # start async export
        result = create_csv_export.apply_async(
            (), {
                'username': username,
                'id_string': id_string,
                'query': query,
                'export_id': export.id
            })
    else:
        raise Export.ExportTypeError
    if result:
        export.task_id = result.task_id
        export.save()
        return export, result
    return None


@task()
def create_xls_export(username, id_string, query=None, force_xlsx=False,
                      export_id=None):
    # we re-query the db instead of passing model objects according to
    # http://docs.celeryproject.org/en/latest/userguide/tasks.html#state
    ext = 'xls' if not force_xlsx else 'xlsx'

    # though export is not available when for has 0 submissions, we
    # catch this since it potentially stops celery
    try:
        export = generate_export(Export.XLS_EXPORT, ext, username, id_string,
            export_id, query)
    except Exception:
        return None
    else:
        return export

@task()
def create_csv_export(username, id_string, query=None,
                      export_id=None):
    # we re-query the db instead of passing model objects according to
    # http://docs.celeryproject.org/en/latest/userguide/tasks.html#state
    try:
        # though export is not available when for has 0 submissions, we
        # catch this since it potentially stops celery
        export = generate_export(Export.CSV_EXPORT, 'csv', username, id_string,
            export_id, query)
    except Exception:
        return None
    else:
        return export