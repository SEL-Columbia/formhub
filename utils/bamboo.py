
import StringIO
import unicodecsv

from pybamboo.dataset import Dataset
from pybamboo.connection import Connection
from pybamboo.exceptions import ErrorParsingBambooData

from odk_viewer.models import ParsedInstance
from odk_viewer.pandas_mongo_bridge import (CSVDataFrameBuilder,
                                            NoRecordsFoundError)
from restservice.models import RestService


def get_bamboo_url(xform):
    try:
        service = list(RestService.objects.filter(xform=xform, name='bamboo')).pop()
    except IndexError:
        return 'http://bamboo.io'

    return service.service_url


def delete_bamboo_dataset(xform):
    if not xform.bamboo_dataset:
        return False
    try:
        dataset = Dataset(connection=Connection(url=get_bamboo_url(xform)),
                          dataset_id=xform.bamboo_dataset)
        return dataset.delete()
    except ErrorParsingBambooData:
        return False


def ensure_rest_service(xform):
    ''' creates Bamboo RestService if doesn't exist '''
    bb_url = get_bamboo_url(xform)
    services = RestService.objects.filter(xform=xform, name='bamboo')

    # do nothing if there's already a restservice for that.
    if services.filter(service_url=bb_url).count():
        return True

    # there is no service ; let's create a default one.
    if not services.count():
        RestService.objects.create(xform=xform,
                                   name='bamboo',
                                   service_url=bb_url)
        return True

    # we have existing services with non-default URL
    # do nothing as the user probably knows what to do.
    return False


def get_new_bamboo_dataset(xform, force_last=False):

    dataset_id = u''

    try:
        content_data = get_csv_data(xform, force_last=force_last)
        dataset = Dataset(connection=Connection(url=get_bamboo_url(xform)),
                          content=content_data,
                          na_values=['n/a'])
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

            w = unicodecsv.DictWriter(csv_buf, fieldnames=headers_to_use,
                                      extrasaction='ignore',
                                      lineterminator='\n',
                                      encoding='utf-8')
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
                                                xform.id_string)
    try:
        csv_dataframe_builder.export_to(buff)
        if force_last:
            # requested to add last submission to the buffer
            buff.write(get_csv_data_manual(xform,
                                           only_last=True, with_header=False,
                                           headers_to_use=
                                           get_headers_from(buff)))
    except NoRecordsFoundError:
        # verify that we don't have a single submission before giving up
        get_csv_data_manual(xform, with_header=True)

    if buff.len:
        # rewrite CSV header so that meta fields (starting with _ or meta)
        # are prefixed to ensure that the dataset will be joinable to
        # another formhub dataset

        prefix = (u'%(id_string)s_%(id)s'
                  % {'id_string': xform.id_string, 'id': xform.id})

        new_buff = getbuff()
        buff.seek(0)
        reader = unicodecsv.reader(buff, encoding='utf-8')
        writer = unicodecsv.writer(new_buff, encoding='utf-8')

        is_header = True

        for row in reader:
            if is_header:
                is_header = False
                for idx, col in enumerate(row):
                    if col.startswith('_') or col.startswith('meta_')\
                            or col.startswith('meta/'):
                        row[idx] = (u'%(prefix)s%(col)s'
                                    % {'prefix': prefix, 'col': col})
            writer.writerow(row)

        return new_buff.getvalue()
    else:
        raise NoRecordsFoundError
