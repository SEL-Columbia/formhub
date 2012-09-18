from celery import task
from odk_viewer.models.export import XLS_EXPORT, CSV_EXPORT, KML_EXPORT, generate_export


@task()
def create_xls_export(username, id_string, query=None, force_xlsx=False,
                      export_id=None):
    # we re-query the db instead of passing model objects according to
    # http://docs.celeryproject.org/en/latest/userguide/tasks.html#state
    ext = 'xls' if not force_xlsx else 'xlsx'

    # though export is not available when for has 0 submissions, we
    # catch this since it potentially stops celery
    try:
        export = generate_export(XLS_EXPORT, ext, username, id_string, export_id, query)
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
        export = generate_export(CSV_EXPORT, 'csv', username, id_string, export_id, query)
    except Exception:
        return None
    else:
        return export