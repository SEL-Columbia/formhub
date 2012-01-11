from django.core.management.base import BaseCommand
from odk_viewer.models import DataDictionary

class Command(BaseCommand):
    help = "This is a one-time command to mark start times of old surveys."

    def handle(self, *args, **kwargs):
        for dd in DataDictionary.objects.all():
            try:
                dd._mark_start_time_boolean()
                dd.save()
            except Exception, e:
                print "Could not mark start time for DD: %s" % repr(dd)