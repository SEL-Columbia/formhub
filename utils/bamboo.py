
import json
import StringIO

import requests
from pybamboo.dataset import Dataset
from pybamboo.connection import Connection

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

    csv_dataframe_builder = CSVDataFrameBuilder(xform.user.username,
                                                xform.id_string, '')
    buff = StringIO.StringIO()

    # might raise NoRecordsFoundError
    csv_dataframe_builder.export_to(buff)

    if not buff.len:
        raise NoRecordsFoundError

    return buff
