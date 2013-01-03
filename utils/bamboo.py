
import json
import StringIO

import requests

from odk_viewer.pandas_mongo_bridge import (CSVDataFrameBuilder,
                                            NoRecordsFoundError)
from restservice.models import RestService


def get_bamboo_url(xform):
    try:
        service = RestService.objects.get(xform=xform, name='bamboo')
    except RestService.DoesNotExist:
        return 'http://bamboo.io'

    return service.service_url

def add_bamboo_restservice(xform, url):
    try:
        RestService.objects.get(xform=xform, name='bamboo', service_url=url)
    except RestService.DoesNotExist:
        service = RestService(name='bamboo', xform=xform, service_url=url)
        service.service_url = url
        service.save()


def get_new_bamboo_dataset(xform):

    dataset_id = u''
    url_data = {'url_root': get_bamboo_url(xform)}
    url = '%(url_root)s/datasets' % url_data

    try:
        csv_data = get_csv_data(xform)
    except NoRecordsFoundError:
        return dataset_id

    req = requests.post(url, files={'csv_file': csv_data.getvalue()})

    if req.status_code in (200, 201, 202):
        try:
            dataset_id = json.loads(req.text).get('id')
        except:
            pass
        else:
            add_bamboo_restservice(xform, url_data['url_root'])
    return dataset_id


def get_csv_data(xform):
    
    csv_dataframe_builder = CSVDataFrameBuilder(xform.user.username,
                                                xform.id_string, '')
    buff = StringIO.StringIO()
    
    # might raise NoRecordsFoundError
    csv_dataframe_builder.export_to(buff)
    return buff
