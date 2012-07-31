import httplib2
from restservice.RestServiceInterface import RestServiceInterface
import json

class ServiceDefinition(RestServiceInterface):
    id = u'json'

    def send(self, url, instance):
        post_data = dumps(instance.xform.id_string)
        headers = {"Content-Type": "application/json"}
        http = httplib2.Http()
        resp, content = http.request(uri=url, method='POST',headers=headers
                                     body=post_data)
        

