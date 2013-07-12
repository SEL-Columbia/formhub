#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 fileencoding=utf-8
import json
from django.conf import settings
from django.core.management import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.translation import ugettext_lazy
from odk_logger.models import Instance


class Command(BaseCommand):
    help = ugettext_lazy("Fixes deleted instances by syncing "
                         "deleted items from mongo.")

    def handle(self, *args, **kwargs):
        # Reset all sql deletes to None
        Instance.objects.exclude(
            deleted_at=None, xform__downloadable=True).update(deleted_at=None)

        # Get all mongo deletes
        query = '{"$and": [{"_deleted_at": {"$exists": true}}, ' \
                '{"_deleted_at": {"$ne": null}}]}'
        query = json.loads(query)
        xform_instances = settings.MONGO_DB.instances
        cursor = xform_instances.find(query)
        for record in cursor:
            # update sql instance with deleted_at datetime from mongo
            try:
                i = Instance.objects.get(
                    uuid=record["_uuid"],  xform__downloadable=True)
            except Instance.DoesNotExist:
                continue
            else:
                deleted_at = parse_datetime(record["_deleted_at"])
                if not timezone.is_aware(deleted_at):
                    deleted_at = timezone.make_aware(
                        deleted_at, timezone.utc)
                i.set_deleted(deleted_at)
