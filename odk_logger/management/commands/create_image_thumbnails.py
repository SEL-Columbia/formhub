#!/usr/bin/env python
from optparse import make_option
from django.contrib.auth.models import User

from django.core.management.base import BaseCommand, CommandError
from django.core.files.storage import get_storage_class
from django.conf import settings

from odk_logger.models.attachment import Attachment
from odk_logger.models.xform import XForm
from utils.image_tools import get_dimensions, resize, resize_local_env
from utils.model_tools import queryset_iterator
from utils.viewer_tools import get_path
from django.utils.translation import ugettext as _, ugettext_lazy


class Command(BaseCommand):
    help = ugettext_lazy("Creates thumbnails for "
                         "all form images and stores them")
    option_list = BaseCommand.option_list + (
        make_option('-u', '--username',
            help=ugettext_lazy("Username of the form user")),
        make_option('-i', '--id_string',
            help=ugettext_lazy("id string of the form"))
    )

    def handle(self, *args, **kwargs):
        attachments_qs = Attachment.objects.select_related(
            'instance', 'instance__xform')
        if kwargs.get('username'):
            username = kwargs.get('username')
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise CommandError(
                    "Error: username %(username)s does not exist" %
                    {'username': username}
                )
            attachments_qs = attachments_qs.filter(instance__user=user)
        if kwargs.get('id_string'):
            id_string = kwargs.get('id_string')
            try:
                xform = XForm.objects.get(id_string=id_string)
            except XForm.DoesNotExist:
                raise CommandError(
                    "Error: Form with id_string %(id_string)s does not exist" %
                    {'id_string': id_string}
                )
            attachments_qs = attachments_qs.filter(instance__xform=xform)
        fs = get_storage_class('django.core.files.storage.FileSystemStorage')()
        for att in queryset_iterator(attachments_qs):
            filename = att.media_file.name
            default_storage = get_storage_class()()
            if not default_storage.exists(get_path(filename,
                                    settings.THUMB_CONF['small']['suffix'])):
                try:
                    if default_storage.__class__ != fs.__class__:
                        resize(filename)
                    else:
                        resize_local_env(filename)
                    if default_storage.exists(get_path(filename,
                            '%s' % settings.THUMB_CONF['small']['suffix'])):
                        print (_(u'Thumbnails created for %(file)s') 
                               % {'file': filename})
                    else:
                        print (_(u'Problem with the file %(file)s') 
                               % {'file': filename})
                except (IOError, OSError), e:
                    print _(u'Error on %(filename)s: %(error)s') \
                            % {'filename': filename, 'error': e}
