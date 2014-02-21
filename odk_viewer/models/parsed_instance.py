import base64
import datetime
import re
import json

from dateutil import parser
from bson import json_util
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save, pre_delete
from restservice.utils import call_service
from stats.tasks import stat_log
from utils.decorators import apply_form_field_names
from utils.model_tools import queryset_iterator
from odk_logger.models import Instance, XForm
from celery import task
from common_tags import START_TIME, START, END_TIME, END, ID, UUID,\
    ATTACHMENTS, GEOLOCATION, SUBMISSION_TIME, MONGO_STRFTIME,\
    BAMBOO_DATASET_ID, DELETEDAT, TAGS
from django.utils.translation import ugettext as _


# this is Mongo Collection where we will store the parsed submissions
xform_instances = settings.MONGO_DB.instances
key_whitelist = ['$or', '$and', '$exists', '$in', '$gt', '$gte',
                 '$lt', '$lte', '$regex', '$options', '$all']
GLOBAL_SUBMISSION_STATS = u'global_submission_stats'
DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'


class ParseError(Exception):
    pass


def datetime_from_str(text):
    # Assumes text looks like 2011-01-01T09:50:06.966
    if text is None:
        return None
    dt = None
    try:
        dt = parser.parse(text)
    except Exception:
        return None
    return dt


def dict_for_mongo(d):
    for key, value in d.items():
        if type(value) == list:
            value = [dict_for_mongo(e)
                     if type(e) == dict else e for e in value]
        elif type(value) == dict:
            value = dict_for_mongo(value)
        elif key == '_id':
            try:
                d[key] = int(value)
            except ValueError:
                # if it is not an int don't convert it
                pass
        if _is_invalid_for_mongo(key):
            del d[key]
            d[_encode_for_mongo(key)] = value
    return d


def _encode_for_mongo(key):
    return reduce(lambda s, c: re.sub(c[0], base64.b64encode(c[1]), s),
                  [(r'^\$', '$'), (r'\.', '.')], key)


def _decode_from_mongo(key):
    re_dollar = re.compile(r"^%s" % base64.b64encode("$"))
    re_dot = re.compile(r"\%s" % base64.b64encode("."))
    return reduce(lambda s, c: c[0].sub(c[1], s),
                  [(re_dollar, '$'), (re_dot, '.')], key)


def _is_invalid_for_mongo(key):
    return not key in \
        key_whitelist and (key.startswith('$') or key.count('.') > 0)


@task
def update_mongo_instance(record):
    # since our dict always has an id, save will always result in an upsert op
    # - so we dont need to worry whether its an edit or not
    # http://api.mongodb.org/python/current/api/pymongo/collection.html#pymongo.collection.Collection.save
    try:
        return xform_instances.save(record)
    except Exception:
        # todo: mail admins about the exception
        pass


class ParsedInstance(models.Model):
    USERFORM_ID = u'_userform_id'
    STATUS = u'_status'
    DEFAULT_LIMIT = 30000
    DEFAULT_BATCHSIZE = 1000

    instance = models.OneToOneField(Instance, related_name="parsed_instance")
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)
    # TODO: decide if decimal field is better than float field.
    lat = models.FloatField(null=True)
    lng = models.FloatField(null=True)

    class Meta:
        app_label = "odk_viewer"

    @classmethod
    @apply_form_field_names
    def query_mongo(cls, username, id_string, query, fields, sort, start=0,
                    limit=DEFAULT_LIMIT, count=False, hide_deleted=True):
        fields_to_select = {cls.USERFORM_ID: 0}
        # TODO: give more detailed error messages to 3rd parties
        # using the API when json.loads fails
        query = json.loads(
            query, object_hook=json_util.object_hook) if query else {}
        query = dict_for_mongo(query)
        query[cls.USERFORM_ID] = u'%s_%s' % (username, id_string)
        if hide_deleted:
            #display only active elements
            # join existing query with deleted_at_query on an $and
            query = {"$and": [query, {"_deleted_at": None}]}
        # fields must be a string array i.e. '["name", "age"]
        fields = json.loads(
            fields, object_hook=json_util.object_hook) if fields else []
        # TODO: current mongo (2.0.4 of this writing)
        # cant mix including and excluding fields in a single query
        if type(fields) == list and len(fields) > 0:
            fields_to_select = dict(
                [(_encode_for_mongo(field), 1) for field in fields])
        sort = json.loads(
            sort, object_hook=json_util.object_hook) if sort else {}
        cursor = xform_instances.find(query, fields_to_select)
        if count:
            return [{"count": cursor.count()}]

        if start < 0 or limit < 0:
            raise ValueError(_("Invalid start/limit params"))

        cursor.skip(start).limit(limit)
        if type(sort) == dict and len(sort) == 1:
            sort_key = sort.keys()[0]
            #todo: encode sort key if it has dots
            sort_dir = int(sort[sort_key])  # -1 for desc, 1 for asc
            cursor.sort(_encode_for_mongo(sort_key), sort_dir)
        # set batch size
        cursor.batch_size = cls.DEFAULT_BATCHSIZE
        return cursor

    @classmethod
    @apply_form_field_names
    def query_mongo_minimal(
            cls, query, fields, sort, start=0, limit=DEFAULT_LIMIT,
            count=False, hide_deleted=True):
        fields_to_select = {cls.USERFORM_ID: 0}
        # TODO: give more detailed error messages to 3rd parties
        # using the API when json.loads fails
        query = json.loads(
            query, object_hook=json_util.object_hook) if query else {}
        query = dict_for_mongo(query)
        if hide_deleted:
            #display only active elements
            # join existing query with deleted_at_query on an $and
            query = {"$and": [query, {"_deleted_at": None}]}
        # fields must be a string array i.e. '["name", "age"]'
        fields = json.loads(
            fields, object_hook=json_util.object_hook) if fields else []
        # TODO: current mongo (2.0.4 of this writing)
        # cant mix including and excluding fields in a single query
        if type(fields) == list and len(fields) > 0:
            fields_to_select = dict(
                [(_encode_for_mongo(field), 1) for field in fields])
        sort = json.loads(
            sort, object_hook=json_util.object_hook) if sort else {}
        cursor = xform_instances.find(query, fields_to_select)
        if count:
            return [{"count": cursor.count()}]

        if start < 0 or limit < 0:
            raise ValueError(_("Invalid start/limit params"))

        cursor.skip(start).limit(limit)
        if type(sort) == dict and len(sort) == 1:
            sort_key = sort.keys()[0]
            #todo: encode sort key if it has dots
            sort_dir = int(sort[sort_key])  # -1 for desc, 1 for asc
            cursor.sort(_encode_for_mongo(sort_key), sort_dir)
        # set batch size
        cursor.batch_size = cls.DEFAULT_BATCHSIZE
        return cursor

    def to_dict_for_mongo(self):
        d = self.to_dict()
        data = {
            UUID: self.instance.uuid,
            ID: self.instance.id,
            BAMBOO_DATASET_ID: self.instance.xform.bamboo_dataset,
            self.USERFORM_ID: u'%s_%s' % (
                self.instance.user.username,
                self.instance.xform.id_string),
            ATTACHMENTS: [a.media_file.name for a in
                          self.instance.attachments.all()],
            self.STATUS: self.instance.status,
            GEOLOCATION: [self.lat, self.lng],
            SUBMISSION_TIME: self.instance.date_created.strftime(MONGO_STRFTIME),
            TAGS: list(self.instance.tags.names())
        }
        if isinstance(self.instance.deleted_at, datetime.datetime):
            data[DELETEDAT] = self.instance.deleted_at.strftime(MONGO_STRFTIME)
        d.update(data)
        return dict_for_mongo(d)

    def update_mongo(self, async=True):
        d = self.to_dict_for_mongo()
        if async:
            update_mongo_instance.apply_async((), {"record": d})
        else:
            update_mongo_instance(d)

    def to_dict(self):
        if not hasattr(self, "_dict_cache"):
            self._dict_cache = self.instance.get_dict()
        return self._dict_cache

    @classmethod
    def dicts(cls, xform):
        qs = cls.objects.filter(instance__xform=xform)
        for parsed_instance in queryset_iterator(qs):
            yield parsed_instance.to_dict()

    def _get_name_for_type(self, type_value):
        """
        We cannot assume that start time and end times always use the same
        XPath. This is causing problems for other peoples' forms.

        This is a quick fix to determine from the original XLSForm's JSON
        representation what the 'name' was for a given
        type_value ('start' or 'end')
        """
        datadict = json.loads(self.instance.xform.json)
        for item in datadict['children']:
            if type(item) == dict and item.get(u'type') == type_value:
                return item['name']

    def get_data_dictionary(self):
        # todo: import here is a hack to get around a circular import
        from odk_viewer.models import DataDictionary
        return DataDictionary.objects.get(
            user=self.instance.xform.user,
            id_string=self.instance.xform.id_string
        )

    data_dictionary = property(get_data_dictionary)

    # TODO: figure out how much of this code should be here versus
    # data_dictionary.py.
    def _get_geopoint(self):
        doc = self.to_dict()
        xpath = self.data_dictionary.xpath_of_first_geopoint()
        text = doc.get(xpath, u'')
        return dict(
            zip(
                [u'latitude', u'longitude', u'altitude', u'accuracy'],
                text.split()
            )
        )

    def _set_geopoint(self):
        g = self._get_geopoint()
        self.lat = g.get(u'latitude')
        self.lng = g.get(u'longitude')
        # update xform incase we have a latitude
        xform = XForm.objects.select_related().select_for_update()\
            .get(pk=self.instance.xform.pk)
        if self.lat is not None and not xform.surveys_with_geopoints:
            xform.surveys_with_geopoints = True
            xform.save()

    def save(self, async=False, *args, **kwargs):
        self.start_time = None  # start/end_time obsolete: originally used to approximate for instanceID,
        self.end_time = None    # before instanceIDs were implemented
        self._set_geopoint()
        super(ParsedInstance, self).save(*args, **kwargs)
        # insert into Mongo
        self.update_mongo(async)


def _remove_from_mongo(sender, **kwargs):
    instance_id = kwargs.get('instance').instance.id
    xform_instances.remove(instance_id)

pre_delete.connect(_remove_from_mongo, sender=ParsedInstance)


def rest_service_form_submission(sender, **kwargs):
    parsed_instance = kwargs.get('instance')
    created = kwargs.get('created')
    if created:
        call_service(parsed_instance)


post_save.connect(rest_service_form_submission, sender=ParsedInstance)


def submission_count(sender, **kwargs):
    parsed_instance = kwargs.get('instance')
    created = kwargs.get('created')
    if created:
        stat_log.delay(GLOBAL_SUBMISSION_STATS, 1)
        key = '%(username)s_%(xform_id_string)s_submissions'\
            % {"username": parsed_instance.instance.xform.user.username,
               "xform_id_string": parsed_instance.instance.xform.id_string}
        stat_log.delay(key, 1)

post_save.connect(submission_count, sender=ParsedInstance)
