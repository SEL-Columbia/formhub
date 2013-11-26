#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 fileencoding=utf-8

from django.core.management.base import BaseCommand
from django.utils.translation import ugettext_lazy
from odk_logger.models import XForm
from odk_viewer.models import ParsedInstance
from utils.model_tools import queryset_iterator


class Command(BaseCommand):
    help = ugettext_lazy("Import a folder of XForms for ODK.")

    def handle(self, *args, **kwargs):
        xforms = XForm.objects.all()
        total = xforms.count()
        count = 0
        for xform in queryset_iterator(XForm.objects.all()):
            has_geo = ParsedInstance.objects.filter(
                instance__xform=xform, lat__isnull=False).count() > 0
            try:
                xform.surveys_with_geopoints = has_geo
                xform.save()
            except Exception as e:
                print e
            else:
                count += 1
        print "%d of %d forms processed." % (count, total)
