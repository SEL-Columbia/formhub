from datetime import datetime
from django.conf import settings
from odk_viewer.models.parsed_instance import dict_for_mongo, _encode_for_mongo

audit = settings.MONGO_DB.auditlog
DEFAULT_LIMIT = 1000

class AuditLog(object):
    ACCOUNT = u"account"
    DEFAULT_BATCHSIZE = 1000
    CREATED_ON = u"created_on"
    def __init__(self, data):
        self.data = data

    def save(self):
        return audit.save(self.data)

    @classmethod
    def query_mongo(cls, username, query, fields, sort, start=0,
                    limit=DEFAULT_LIMIT, count=False):
        query = dict_for_mongo(query)
        query[cls.ACCOUNT] = username
        # todo: if created on in query, convert to datetime object
        #if query[cls.CREATED_ON]:
        #    query[cls.CREATED_ON] = datetime.strptime(query[cls.CREATED_ON]["$gt"])

        # TODO: current mongo (2.0.4 of this writing)
        # cant mix including and excluding fields in a single query
        fields_to_select = None
        if type(fields) == list and len(fields) > 0:
            fields_to_select = dict([(_encode_for_mongo(field), 1) for field in fields])
        cursor = audit.find(query, fields_to_select)
        if count:
            return [{"count":cursor.count()}]

        cursor.skip(start).limit(limit)
        if type(sort) == dict and len(sort) == 1:
            sort_key = sort.keys()[0]
            #todo: encode sort key if it has dots
            sort_dir = int(sort[sort_key])  # -1 for desc, 1 for asc
            cursor.sort(_encode_for_mongo(sort_key), sort_dir)
        # set batch size for cursor iteration
        cursor.batch_size = cls.DEFAULT_BATCHSIZE
        return cursor