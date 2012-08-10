
import json
import StringIO

import requests

from odk_viewer.pandas_mongo_bridge import (CSVDataFrameBuilder,
                                            NoRecordsFoundError)
from restservice.models import RestService


def get_bamboo_url(xform):
    service = RestService.objects.get(xform=xform, name='bamboo')
    return service.service_url


def get_new_bamboo_dataset(xform):

    dataset_id = u''

    try:
        url = '%(url_root)s/datasets' % {'url_root': get_bamboo_url(xform)}
    except RestService.DoesNotExists:
        return dataset_id

    try:
        csv_data = get_csv_data(xform)
    except NoRecordsFoundError:
        return dataset_id

    req = requests.post(url, files={'data.csv': csv_data.read()})

    if req.status in (200, 201, 202):
        try:
            dataset_id = json.loads(req.text).get('id')
        except:
            pass
    return dataset_id


def get_csv_data(xform):
    
    csv_dataframe_builder = CSVDataFrameBuilder(xform.user.username,
                                                xform.id_string, '')
    buff = StringIO.StringIO()
    
    # might raise NoRecordsFoundError
    csv_dataframe_builder.export_to(buff)
    return buff