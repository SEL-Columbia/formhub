from .instance import xform_instances, Instance
from .xform import XForm
from .surveyor import Surveyor
from .phone import Phone
from .district import District
from .attachment import Attachment
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

    try:
        instance, created = Instance.objects.get_or_create(xml=xml)
        if created:
            for f in media_files:
                Attachment.objects.create(instance=instance, attachment=f)
        return instance, created
    except XForm.DoesNotExist:
        utils.report_exception("Missing XForm", "TRY TO GET ID HERE")
