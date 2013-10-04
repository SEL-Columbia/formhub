import django.dispatch

from odk_logger.models import XForm

xform_tags_added = django.dispatch.Signal(providing_args=['xform', 'tags'])


@django.dispatch.receiver(xform_tags_added, sender=XForm)
def add_tags_to_xform(sender, **kwargs):
    xform = kwargs.get('xform', None)
    tags = kwargs.get('tags', None)
    if isinstance(xform, XForm) and isinstance(tags, list):
        # update existing instances with the new tag
        for instance in xform.surveys.all():
            for tag in tags:
                if tag not in instance.tags.names():
                    instance.tags.add(tag)
            # ensure mongodb is updated
            instance.parsed_instance.save()
