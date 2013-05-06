import os
import mimetypes

from tempfile import NamedTemporaryFile
from hashlib import md5
from django.core.files.storage import get_storage_class
from django.db import models

from instance import Instance


def upload_to(instance, filename):
    return os.path.join(
        instance.instance.user.username,
        'attachments',
        os.path.split(filename)[1])


class Attachment(models.Model):
    instance = models.ForeignKey(Instance, related_name="attachments")
    media_file = models.FileField(upload_to=upload_to)
    mimetype = models.CharField(
        max_length=50, null=False, blank=True, default='')

    class Meta:
        app_label = 'odk_logger'

    def save(self, *args, **kwargs):
        if self.media_file and self.mimetype == '':
            # guess mimetype
            mimetype, encoding = mimetypes.guess_type(self.media_file.name)
            if mimetype:
                self.mimetype = mimetype
        super(Attachment, self).save(*args, **kwargs)

    @property
    def full_filepath(self):
        if self.media_file:
            default_storage = get_storage_class()()
            try:
                return default_storage.path(self.media_file.name)
            except NotImplementedError:
                # read file from s3
                name, ext = os.path.splitext(self.media_file.name)
                tmp = NamedTemporaryFile(suffix=ext, delete=False)
                f = default_storage.open(self.media_file.name)
                tmp.write(f.read())
                tmp.close()
                return tmp.name
        return None

    @property
    def file_hash(self):
        if self.media_file.storage.exists(self.media_file.name):
            return u'%s' % md5(self.media_file.read()).hexdigest()
        return u''

    @property
    def filename(self):
        return os.path.basename(self.media_file.name)
