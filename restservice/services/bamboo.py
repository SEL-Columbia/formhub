
from pybamboo.dataset import Dataset
from pybamboo.connection import Connection

from restservice.RestServiceInterface import RestServiceInterface
from utils.bamboo import get_new_bamboo_dataset, get_bamboo_url


class ServiceDefinition(RestServiceInterface):
    id = u'bamboo'
    verbose_name = u'bamboo POST'

    def send(self, url, parsed_instance):

        xform = parsed_instance.instance.xform
        rows = [parsed_instance.to_dict_for_mongo()]

        # prefix meta columns names for bamboo
        prefix = (u'%(id_string)s_%(id)s'
                  % {'id_string': xform.id_string, 'id': xform.id})

        for row in rows:
            for col, value in row.items():
                if col.startswith('_') or col.startswith('meta_') \
                    or col.startswith('meta/'):
                    new_col = (u'%(prefix)s%(col)s'
                               % {'prefix': prefix, 'col': col})
                    row.update({new_col: value})
                    del(row[col])

        # create dataset on bamboo first (including current submission)
        if not xform.bamboo_dataset:
            dataset_id = get_new_bamboo_dataset(xform, force_last=True)
            xform.bamboo_dataset = dataset_id
            xform.save()
        else:
            dataset = Dataset(connection=Connection(url=get_bamboo_url(xform)),
                              dataset_id=xform.bamboo_dataset)
            dataset.update_data(rows=rows)
