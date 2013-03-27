import httplib2
from restservice.RestServiceInterface import RestServiceInterface


class ServiceDefinition(RestServiceInterface):
    id = u'xml'
    verbose_name = u'XML POST'

    def send(self, url, parsed_instance):
        instance = parsed_instance.instance
        headers = {"Content-Type": "application/xml"}
        http = httplib2.Http()
        resp, content = http.request(
            url, method="POST", body=instance.xml, headers=headers)
