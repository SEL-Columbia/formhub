from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.translation import ugettext_lazy, ugettext as _

from odk_viewer.models import ParsedInstance
from utils.model_tools import queryset_iterator

class Command(BaseCommand):
    help = ugettext_lazy("Insert all existing parsed instances into MongoDB")

    def handle(self, *args, **kwargs):
        for i, pi in enumerate(queryset_iterator(ParsedInstance.objects.all())):
            pi.update_mongo()
            if (i + 1) % 1000 == 0:
                print (_('Updated %(nb)d records, flushing MongoDB...') 
                       % {'nb': i})
                settings._MONGO_CONNECTION.admin.command({'fsync': 1})
