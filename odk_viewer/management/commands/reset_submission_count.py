from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from optparse import make_option
from django.utils.translation import ugettext_lazy, ugettext as _
from odk_logger.models import XForm
from odk_logger.models.instance import Instance

class Command(BaseCommand):
    help = ugettext_lazy('Remove "is_deleted" flag from sql instances')

    def handle(self, *args, **kwargs):
        c = 0
        qs = XForm.objects.all()
        for form in qs:
            count = form.surveys.filter(is_deleted=False).count()
            form.num_of_submissions = count if count > 0 else -1
            form.save()
            c += 1
        print "Updated %d records." % c
