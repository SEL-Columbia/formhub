import httplib2
from restservice.RestServiceInterface import RestServiceInterface


class ServiceDefinition(RestServiceInterface):
    id = u'xml'

    def send(self, url, instance):
        post_data = {'xml_data': instance.xml}
        headers = {"Content-Type": "application/xml"}
        http = httplib2.Http()
        resp, content = http.request(url,body=instance.xml,
                                     headers=headers)
