import gc
import uuid
from odk_logger.models.xform import XForm, DuplicateUUIDError


def generate_uuid_for_form():
    return uuid.uuid4().hex


def set_uuid(obj):
    """
    Only give an object a new UUID if it does not have one.
    """
    if not obj.uuid:
        obj.uuid = generate_uuid_for_form()


def queryset_iterator(queryset, chunksize=100):
    '''''
    Iterate over a Django Queryset.

    This method loads a maximum of chunksize (default: 100) rows in
    its memory at the same time while django normally would load all
    rows in its memory. Using the iterator() method only causes it to
    not preload all the classes.
    '''
    start = 0
    end = chunksize
    while start < queryset.count():
        for row in queryset[start:end]:
            yield row
        start += chunksize
        end += chunksize
        gc.collect()

def update_xform_uuid(username, id_string, new_uuid):
    xform = XForm.objects.get(user__username=username, id_string=id_string)
    # check for duplicate uuid
    count = XForm.objects.filter(uuid=new_uuid).count()
    if count > 0:
        raise DuplicateUUIDError("An xform with uuid: %s already exists" % new_uuid)
    xform.uuid = new_uuid
    xform.save()
    
