import uuid


def generate_uuid_for_form():
    return uuid.uuid4().hex


def set_uuid(obj):
    """
    Only give an object a new UUID if it does not have one.
    """
    if not obj.uuid:
        obj.uuid = generate_uuid_for_form()
