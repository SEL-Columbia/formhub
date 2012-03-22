import base64
import datetime
import re

from django.conf import settings
from django.db import models
from django.db.models.signals import post_save, pre_delete

from utils.model_tools import queryset_iterator
from odk_logger.models import Instance
from common_tags import START_TIME, START, END_TIME, END, ID, UUID, ATTACHMENTS

# this is Mongo Collection where we will store the parsed submissions
xform_instances = settings.MONGO_DB.instances


class ParseError(Exception):
    pass


def datetime_from_str(text):
    # Assumes text looks like 2011-01-01T09:50:06.966
    if text is None:
        return None
    date_time_str = text.split(".")[0]
    return datetime.datetime.strptime(
        date_time_str, '%Y-%m-%dT%H:%M:%S'
        )

def dict_for_mongo(d):
    for key, value in d.items():
        if _is_invalid_for_mongo(key):
            del d[key]
            if type(value) == dict:
                value = dict_for_mongo(value)
            d[_encode_for_mongo(key)] = value
    return d


def _encode_for_mongo(key):
    return reduce(lambda s, c: re.sub(c[0], base64.b64encode(c[1]), s),
            [(r'^\$', '$'), (r'\.', '.')], key)


def _is_invalid_for_mongo(key):
    return (key.startswith('$') or key.count('.') > 0)


class ParsedInstance(models.Model):
    USERFORM_ID = u'_userform_id'
    STATUS = u'_status'
    DEFAULT_LIMIT = 30000

    instance = models.OneToOneField(Instance, related_name="parsed_instance")
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)
    # TODO: decide if decimal field is better than float field.
    lat = models.FloatField(null=True)
    lng = models.FloatField(null=True)

    class Meta:
        app_label = "odk_viewer"

    @classmethod
    def query_mongo(cls, username, id_string, query, start=0,
            limit=DEFAULT_LIMIT):
        query = dict_for_mongo(query)
        query[cls.USERFORM_ID] = u'%s_%s' % (username, id_string)
        return xform_instances.find(query,
                {cls.USERFORM_ID: 0}).skip(start).limit(limit)

    def to_dict_for_mongo(self):
        d = dict_for_mongo(self.to_dict())
        d[self.USERFORM_ID] = u'%s_%s' % (self.instance.user.username,
                self.instance.xform.id_string)
        return d

    def update_mongo(self):
        d = self.to_dict_for_mongo()
        xform_instances.save(d)

    def to_dict(self):
        if not hasattr(self, "_dict_cache"):
            self._dict_cache = self.instance.get_dict()
            self._dict_cache.update(
                {
                    UUID: self.instance.uuid,
                    ID: self.instance.id,
                    ATTACHMENTS: [a.media_file.name for a in\
                            self.instance.attachments.all()],
                    self.STATUS: self.instance.status,
                    }
                )
        return self._dict_cache

    @classmethod
    def dicts(cls, xform):
        qs = cls.objects.filter(instance__xform=xform)
        for parsed_instance in queryset_iterator(qs):
            yield parsed_instance.to_dict()

    def _set_start_time(self):
        doc = self.to_dict()
        if START_TIME in doc:
            date_time_str = doc[START_TIME]
            self.start_time = datetime_from_str(date_time_str)
        elif START in doc:
            date_time_str = doc[START]
            self.start_time = datetime_from_str(date_time_str)
        else:
            self.start_time = None

    def _set_end_time(self):
        doc = self.to_dict()
        if END_TIME in doc:
            date_time_str = doc[END_TIME]
            self.end_time = datetime_from_str(date_time_str)
        elif END in doc:
            date_time_str = doc[END]
            self.end_time = datetime_from_str(date_time_str)
        else:
            self.end_time = None

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
        return dict(zip(
                [u'latitude', u'longitude', u'altitude', u'accuracy'],
                text.split()
                ))

    def _set_geopoint(self):
        g = self._get_geopoint()
        self.lat = g.get(u'latitude')
        self.lng = g.get(u'longitude')

    def save(self, *args, **kwargs):
        self._set_start_time()
        self._set_end_time()
        self._set_geopoint()
        super(ParsedInstance, self).save(*args, **kwargs)
        # insert into Mongo
        self.update_mongo()


def _remove_from_mongo(sender, **kwargs):
    instance_id = kwargs.get('instance').instance.id
    xform_instances.remove(instance_id)

pre_delete.connect(_remove_from_mongo, sender=ParsedInstance)


def _parse_instance(sender, **kwargs):
    # When an instance is saved, first delete the parsed_instance
    # associated with it.
    instance = kwargs["instance"]
    if instance.xform is not None:
        pi, created = ParsedInstance.objects.get_or_create(instance=instance)

post_save.connect(_parse_instance, sender=Instance)
