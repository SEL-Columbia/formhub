from django.core.management.base import BaseCommand
from django.utils.translation import ugettext_lazy, ugettext as _
from odk_viewer.models import DataDictionary


class Command(BaseCommand):
    help = ugettext_lazy("This is a one-time command to "
                         "mark start times of old surveys.")

    def handle(self, *args, **kwargs):
        for dd in DataDictionary.objects.all():
            try:
                dd._mark_start_time_boolean()
                dd.save()
            except Exception, e:
                print (_("Could not mark start time for DD: %(data)s") 
                       % {'data': repr(dd)})