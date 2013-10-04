import django.dispatch

from odk_logger.models import XForm

xform_tags_add = django.dispatch.Signal(providing_args=['xform', 'tags'])
xform_tags_delete = django.dispatch.Signal(providing_args=['xform', 'tag'])


@django.dispatch.receiver(xform_tags_add, sender=XForm)
def add_tags_to_xform_instances(sender, **kwargs):
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


@django.dispatch.receiver(xform_tags_delete, sender=XForm)
def delete_tag_from_xform_instances(sender, **kwargs):
    xform = kwargs.get('xform', None)
    tag = kwargs.get('tag', None)
    if isinstance(xform, XForm) and isinstance(tag, basestring):
        # update existing instances with the new tag
        for instance in xform.surveys.all():
            if tag in instance.tags.names():
                instance.tags.remove(tag)
                # ensure mongodb is updated
                instance.parsed_instance.save()
