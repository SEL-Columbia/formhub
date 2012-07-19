from django.core.management.base import BaseCommand
from django.conf import settings

from odk_viewer.models import DataDictionary
from utils.model_tools import queryset_iterator

class Command(BaseCommand):
    help = "Insert UUID into XML of all existing XForms"

    def handle(self, *args, **kwargs):
        print '%d XForms to update' % DataDictionary.objects.count()
        for i, dd in enumerate(queryset_iterator(DataDictionary.objects.all())):
            if dd.xls:
                dd._set_uuid_in_xml()
                super(DataDictionary, dd).save()
            if (i + 1) % 10 == 0:
                print 'Updated %d XForms...' % i
