
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


def get_new_bamboo_dataset(xform):

    dataset_id = u''

    try:
        dataset = Dataset(connection=Connection(url=get_bamboo_url(xform)),
                          content=get_csv_data(xform))
    except NoRecordsFoundError:
        return dataset_id

    if dataset.id:
        return dataset.id

    return dataset_id


def get_csv_data(xform):

    def getbuff():
        return StringIO.StringIO()

    def get_csv_data_manual(xform):
         # TODO: find out a better way to handle this
        # when form has only one submission, CSVDFB is empty.
        # we still want to create the BB ds with row 1
        # so we extract is and CSV it.
        pifilter = ParsedInstance.objects.filter(instance__xform=xform)

        if pifilter.count() == 0:
            raise NoRecordsFoundError
        else:
            # we should only do it for count == 1 but eh.
            rows = [pi.to_dict_for_mongo() for pi in pifilter]
            cleaned_keys = [key for key in rows[0].keys()
                                if not key.startswith('_')]

            buff = getbuff()
            w = csv.DictWriter(buff, fieldnames=cleaned_keys,
                               extrasaction='ignore', lineterminator='\n')
            w.writeheader()
            w.writerows(rows)
            buff.flush()

            if not buff.len:
                raise NoRecordsFoundError

        return buff

    csv_dataframe_builder = CSVDataFrameBuilder(xform.user.username,
                                                    xform.id_string, '')

    buff = getbuff()

    try:
        csv_dataframe_builder.export_to(buff)
    except NoRecordsFoundError:
        # verify that we don't have a single submission before giving up
        buff = get_csv_data_manual(xform)

    if buff.len:
        return buff.getvalue()
    else:
        raise NoRecordsFoundError

