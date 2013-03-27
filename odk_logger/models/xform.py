import os
import re
import json

from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models.signals import post_save
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy, ugettext as _

from odk_logger.xform_instance_parser import XLSFormError
from utils.stathat_api import stathat_count
from stats.tasks import stat_log

from hashlib import md5


def upload_to(instance, filename):
    return os.path.join(
        instance.user.username,
        'xls',
        os.path.split(filename)[1])


class DuplicateUUIDError(Exception):
    pass


class XForm(models.Model):
    CLONED_SUFFIX = '_cloned'

    xls = models.FileField(upload_to=upload_to, null=True)
    json = models.TextField(default=u'')
    description = models.TextField(default=u'', null=True)
    xml = models.TextField()
    _sdf = models.TextField(null=True)

    user = models.ForeignKey(User, related_name='xforms', null=True)
    shared = models.BooleanField(default=False)
    shared_data = models.BooleanField(default=False)
    downloadable = models.BooleanField(default=True)
    is_crowd_form = models.BooleanField(default=False)

    # the following fields are filled in automatically
    id_string = models.SlugField(
        editable=False, verbose_name=ugettext_lazy("ID")
    )
    title = models.CharField(editable=False, max_length=64)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    has_start_time = models.BooleanField(default=False)
    uuid = models.CharField(max_length=32, default=u'')

    uuid_regex = re.compile(r'(<instance>.*?id="[^"]+">)(.*</instance>)(.*)',
                            re.DOTALL)
    instance_id_regex = re.compile(r'<instance>.*?id="([^"]+)".*</instance>',
                                   re.DOTALL)
    uuid_node_location = 2
    uuid_bind_location = 4
    bamboo_dataset = models.CharField(max_length=60, default=u'')

    class Meta:
        app_label = 'odk_logger'
        unique_together = (("user", "id_string"),)
        verbose_name = ugettext_lazy("XForm")
        verbose_name_plural = ugettext_lazy("XForms")
        ordering = ("id_string",)
        permissions = (
            ("view_xform", _("Can view associated data")),
        )

    def file_name(self):
        return self.id_string + ".xml"

    def url(self):
        return reverse(
            "download_xform",
            kwargs={
                "username": self.user.username,
                "id_string": self.id_string
            }
        )

    def data_dictionary(self):
        from odk_viewer.models import DataDictionary
        return DataDictionary.objects.get(pk=self.pk)

    @property
    def has_surveys_with_geopoints(self):
        return self.data_dictionary().has_surveys_with_geopoints()

    def _set_id_string(self):
        matches = self.instance_id_regex.findall(self.xml)
        if len(matches) != 1:
            raise XLSFormError(_("There should be a single id string."))
        self.id_string = matches[0]

    def _set_title(self):
        text = re.sub(r"\s+", " ", self.xml)
        matches = re.findall(r"<h:title>([^<]+)</h:title>", text)
        if len(matches) != 1:
            raise XLSFormError(_("There should be a single title."), matches)
        self.title = u"" if not matches else matches[0]

    def update(self, *args, **kwargs):
        super(XForm, self).save(*args, **kwargs)

    def save(self, *args, **kwargs):
        self._set_title()
        old_id_string = self.id_string
        self._set_id_string()
        # check if we have an existing id_string,
        # if so, the one must match but only if xform is NOT new
        if self.pk and old_id_string and old_id_string != self.id_string:
            raise XLSFormError(
                _(u"Your updated form's id_string '%(new_id)s' must match "
                  "the existing forms' id_string '%(old_id)s'." %
                  {'new_id': self.id_string, 'old_id': old_id_string}))
        if getattr(settings, 'STRICT', True) and \
                not re.search(r"^[\w-]+$", self.id_string):
            raise XLSFormError(_(u'In strict mode, the XForm ID must be a '
                               'valid slug and contain no spaces.'))
        super(XForm, self).save(*args, **kwargs)

    def __unicode__(self):
        return getattr(self, "id_string", "")

    def submission_count(self):
        return self.surveys.filter(deleted_at=None).count()
    submission_count.short_description = ugettext_lazy("Submission Count")

    def time_of_last_submission(self):
        try:
            return self.surveys.\
                filter(deleted_at=None).latest("date_created").date_created
        except ObjectDoesNotExist:
            pass

    def time_of_last_submission_update(self):
        try:
            # we also consider deleted surveys in this case
            return self.surveys.latest("date_modified").date_modified
        except ObjectDoesNotExist:
            pass

    @property
    def hash(self):
        return u'%s' % md5(self.xml.encode('utf8')).hexdigest()

    @property
    def can_be_replaced(self):
        return self.submission_count() == 0

    @classmethod
    def data_dictionary_to_sdf(cls, data_dictionary):
        BIND_TYPE_TO_SIMPLE_TYPE = {
            'int': 'integer',
            'decimal': 'float',
            'date': 'date',
            'time': 'datetime',
            'dateTime': 'datetime',
            'select': 'list',
            'boolean': 'boolean'
            # everything else is a 'string'
        }
        BIND_TYPE_TO_OLAP = {
            'int': 'measure',
            'decimal': 'measure'
            # everything else is a dimension
        }
        BIND_TYPE_TO_FORMAT = {
            'time': 'hh:mm:ss'
        }
        def parse_to_sdf(bind_type, label):
            sdf = {}
            sdf["label"] = label
            sdf["simpletype"] = BIND_TYPE_TO_SIMPLE_TYPE.get(bind_type, "string")
            sdf["olap_type"] = BIND_TYPE_TO_OLAP.get(bind_type, "dimension")
            format = BIND_TYPE_TO_FORMAT.get(bind_type)
            if format:
                sdf["format"] = format
            return sdf

        from pyxform.question import Question
        elements = [el for el in data_dictionary.survey_elements if\
            isinstance(el, Question)]
        sdf = {}
        for element in elements:
            bind_type = element.bind.get("type")
            label = element.label
            # bamboo converts slashes to underscrore, lets do the same
            key = "_".join(element.get_abbreviated_xpath().split("/"))
            sdf[key] = parse_to_sdf(bind_type, label)
            # if its a geopoint, split it into its components
            if bind_type == "geopoint":
                for part in ["latitude", "longitude", "altitude", "precision"]:
                    sdf["_%s_%s" % (key, part)] = parse_to_sdf(
                        "decimal", "_%s_%s" % (element.name, part))

            # if is a select multiple, create question for each choice
            if bind_type == "select":
                choices = dict([(c.name, c.label) for c in element.children])
                for name, label in choices.iteritems():
                    sdf["%s_%s" % (key, name)] = parse_to_sdf("boolean", label)

        # add _uuid and _submission_time
        # todo: how do we combine this with extra fields from export code
        extra_fields = {'_uuid': 'string', '_submission_time': 'dateTime'}
        for name, bind_type in extra_fields.iteritems():
            sdf[name] = parse_to_sdf(bind_type, name)
        return json.dumps(sdf)

    @property
    def sdf(self):
        if not self._sdf:
            self._sdf = self.data_dictionary_to_sdf(self.data_dictionary())
            self.save()
        return self._sdf


def stats_forms_created(sender, instance, created, **kwargs):
    if created:
        stathat_count('formhub-forms-created')
        stat_log.delay('formhub-forms-created', 1)


post_save.connect(stats_forms_created, sender=XForm)
