import httplib2

from django.utils import simplejson
from odk_viewer.models import ParsedInstance
from restservice.RestServiceInterface import RestServiceInterface


class ServiceDefinition(RestServiceInterface):
    id = u'json'
    verbose_name = u'JSON POST'

    def send(self, url, instance):
        args = {
            'username': instance.xform.user.username,
            'id_string': instance.xform.id_string,
            'query': '{"uuid": "%s"}' % instance.uuid,
            'fields': None,
            'sort': None
        }
        try:
            cursor = ParsedInstance.query_mongo(**args)
        except ValueError, e:
            return
        records = list(record for record in cursor)
        post_data = simplejson.dumps(records)
        headers = {"Content-Type": "application/json"}
        http = httplib2.Http()
        resp, content = http.request(uri=url, method='POST',headers=headers,
                                     body=post_data)

