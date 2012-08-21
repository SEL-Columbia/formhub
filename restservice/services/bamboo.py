
import requests
from django.utils import simplejson

from restservice.RestServiceInterface import RestServiceInterface
from utils.bamboo import get_new_bamboo_dataset


class ServiceDefinition(RestServiceInterface):
    id = u'bamboo'
    verbose_name = u'bamboo POST'

    def send(self, url, parsed_instance):

        xform = parsed_instance.instance.xform

        # create dataset on bamboo first (including current submission)
        if not xform.bamboo_dataset:
            dataset_id = get_new_bamboo_dataset(xform)
            xform.bamboo_dataset = dataset_id
            xform.save()
        else:
            post_data = simplejson.dumps(parsed_instance.to_dict_for_mongo())
            url = ("%(root)sdatasets/%(dataset)s"
            	   % {'root': url,
            	   	  'dataset': parsed_instance.instance.xform.bamboo_dataset})
            requests.post(url, data=post_data,
        				  headers={"Content-Type": "application/json"})

