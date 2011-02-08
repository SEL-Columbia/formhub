from .instance import Instance
from .xform import XForm
from .attachment import Attachment
from .survey_type import SurveyType
from .. import tag, utils

def get_or_create_instance(xml_file, media_files):
    """
    I used to check if this file had been submitted already, I've
    taken this out because it was too slow. Now we're going to create
    a way for an admin to mark duplicate instances. This should
    simplify things a bit.
    """
    xml_file.open()
    xml = xml_file.read()
    xml_file.close()

    instance, created = Instance.objects.get_or_create(xml=xml)
    if created:
        for f in media_files:
            Attachment.objects.create(instance=instance, media_file=f)
    return instance, created
