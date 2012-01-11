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
    existing_instance_count = Instance.objects.filter(xml=xml, user=user).count()
    if existing_instance_count == 0:
        proceed_to_create_instance = True
    else:
        existing_instance = Instance.objects.filter(xml=xml, user=user)[0]
        if not existing_instance.xform.has_start_time:
            proceed_to_create_instance = True
        else:
            # Ignore submission as a duplicate IFF
            #  * a submission's XForm collects start time
            #  * the submitted XML is an exact match with one that
            #    has already been submitted for that user.
            proceed_to_create_instance = False

    if proceed_to_create_instance:
        instance = Instance.objects.create(xml=xml, user=user, status=status)
        for f in media_files:
            Attachment.objects.get_or_create(instance=instance, media_file=f)
        return instance
    return None
