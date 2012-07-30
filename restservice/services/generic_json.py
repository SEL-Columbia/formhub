import httplib2
from restservice.RestServiceInterface import RestServiceInterface


class ServiceDefinition(RestServiceInterface):
    id = u'f2dhis2'

    def send(self, url, instance):
        info = {"id_string": instance.xform.id_string, "uuid": instance.uuid}
        valid_url = url % info
        http = httplib2.Http()
        resp, content = http.request(valid_url, 'GET')

