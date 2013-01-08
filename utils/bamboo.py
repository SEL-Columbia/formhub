
import StringIO
import csv

from pybamboo.dataset import Dataset
from pybamboo.connection import Connection

from odk_viewer.models import ParsedInstance
from odk_viewer.pandas_mongo_bridge import (CSVDataFrameBuilder,
                                            NoRecordsFoundError)
from restservice.models import RestService


def get_bamboo_url(xform):
    try:
        service = RestService.objects.get(xform=xform, name='bamboo')
    except RestService.DoesNotExist:
        return 'http://bamboo.io'

    return service.service_url


def delete_bamboo_dataset(xform):
    dataset = Dataset(connection=Connection(url=get_bamboo_url(xform)),
                      dataset_id=xform.bamboo_dataset)
    return dataset.delete()


def get_new_bamboo_dataset(xform, force_last=False):

    dataset_id = u''

    try:
        content_data = get_csv_data(xform, force_last=force_last)
        dataset = Dataset(connection=Connection(url=get_bamboo_url(xform)),
                          content=content_data)
    except NoRecordsFoundError:
        return dataset_id

    if dataset.id:
        return dataset.id

    return dataset_id


def get_csv_data(xform, force_last=False):

    def getbuff():
        return StringIO.StringIO()

    def get_headers_from(csv_data):
        csv_data.seek(0)
        header_row = csv_data.readline()
        csv_data.read()
        return header_row.split(',')

    def get_csv_data_manual(xform,
                            only_last=False, with_header=True,
                            headers_to_use=None):
        # TODO: find out a better way to handle this
        # when form has only one submission, CSVDFB is empty.
        # we still want to create the BB ds with row 1
        # so we extract is and CSV it.
        pifilter = ParsedInstance.objects.filter(instance__xform=xform) \
                                 .order_by('-instance__date_modified')

        if pifilter.count() == 0:
            raise NoRecordsFoundError
        else:
            # we should only do it for count == 1 but eh.

            csv_buf = getbuff()

            if only_last:
                pifilter = [pifilter[0]]

            rows = [pi.to_dict_for_mongo() for pi in pifilter]

            if headers_to_use is None:
                headers_to_use = [key for key in rows[0].keys()
                                    if not key.startswith('_')]

            w = csv.DictWriter(csv_buf, fieldnames=headers_to_use,
                               extrasaction='ignore', lineterminator='\n')
            if with_header:
                w.writeheader()
            w.writerows(rows)
            csv_buf.flush()

            if not csv_buf.len:
                raise NoRecordsFoundError

            return csv_buf.getvalue()

    # setup an IO stream
    buff = getbuff()

    # prepare/generate a standard CSV export.
    # note that it omits the current submission (if called from rest)
    csv_dataframe_builder = CSVDataFrameBuilder(xform.user.username,
                                                    xform.id_string, '')
    try:
        csv_dataframe_builder.export_to(buff)
        if force_last:
            # requested to add last submission to the buffer
            buff.write(get_csv_data_manual(xform,
                                           only_last=True, with_header=False,
                                           headers_to_use=get_headers_from(buff)))
    except NoRecordsFoundError:
        # verify that we don't have a single submission before giving up
        get_csv_data_manual(xform, with_header=True)

    if buff.len:
        return buff.getvalue()
    else:
        raise NoRecordsFoundError

