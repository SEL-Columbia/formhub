# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

from .instance import Instance
from .xform import XForm
from .attachment import Attachment
from .survey_type import SurveyType


def get_or_create_instance(username, xml_file, media_files, status=u'submitted_via_web'):
    """
    I used to check if this file had been submitted already, I've
    taken this out because it was too slow. Now we're going to create
    a way for an admin to mark duplicate instances. This should
    simplify things a bit.
    """
    xml_file.open()
    xml = xml_file.read()
    xml_file.close()

    user = get_object_or_404(User, username=username)
    instance, created = Instance.objects.get_or_create(xml=xml, user=user)
    if created:
        instance.status = status
        instance.save()
    if instance.attachments.count() != len(media_files):
        qs = instance.attachments.all()
        qs.delete()
        for f in media_files:
            Attachment.objects.create(instance=instance, media_file=f)
    return instance, created
