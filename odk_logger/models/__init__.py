# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.db import transaction

from .instance import Instance
from .xform import XForm
from .attachment import Attachment
from .survey_type import SurveyType


@transaction.commit_on_success
def create_instance(username, xml_file, media_files, status=u'submitted_via_web'):
    """
    I used to check if this file had been submitted already, I've
    taken this out because it was too slow. Now we're going to create
    a way for an admin to mark duplicate instances. This should
    simplify things a bit.
    """
    xml = xml_file.read()
    xml_file.close()
    user = get_object_or_404(User, username=username)

    instance = Instance.objects.create(xml=xml, user=user, status=status)
    for f in media_files:
        Attachment.objects.create(instance=instance, media_file=f)
    return instance
