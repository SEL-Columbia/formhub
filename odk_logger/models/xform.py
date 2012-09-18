import os
import re

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.query import QuerySet
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy, ugettext as _

from odk_logger.xform_instance_parser import XLSFormError
from utils.stathat_api import stathat_count

from hashlib import md5


def upload_to(instance, filename):
    return os.path.join(
        instance.user.username,
        'xls',
        os.path.split(filename)[1])


class XForm(models.Model):
    CLONED_SUFFIX = '_cloned'

    xls = models.FileField(upload_to=upload_to, null=True)
    json = models.TextField(default=u'')
    description = models.TextField(default=u'', null=True)
    xml = models.TextField()

    user = models.ForeignKey(User, related_name='xforms', null=True)
    shared = models.BooleanField(default=False)
    shared_data = models.BooleanField(default=False)
    downloadable = models.BooleanField(default=True)
    is_crowd_form =  models.BooleanField(default=False)

    # the following fields are filled in automatically
    id_string = models.SlugField(
        editable=False, verbose_name=ugettext_lazy("ID")
    )
    title = models.CharField(editable=False, max_length=64)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    has_start_time = models.BooleanField(default=False)
    uuid = models.CharField(max_length=32, default=u'')

    uuid_regex = re.compile(r'(<instance>.*id="[^"]+">)(.*</instance>)(.*)',
                            re.DOTALL)
    instance_id_regex = re.compile(r'<instance>.*id="([^"]+)".*</instance>',
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
        self._set_id_string()
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
        if self.submission_count() > 0:
            return self.surveys.order_by("-date_created")[0].date_created

    @property
    def hash(self):
        return u'%s' % md5(self.xml.encode('utf8')).hexdigest()


def stathat_forms_created(sender, instance, created, **kwargs):
    if created:
        stathat_count('formhub-forms-created')


post_save.connect(stathat_forms_created, sender=XForm)
