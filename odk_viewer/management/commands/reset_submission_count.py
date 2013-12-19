from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from optparse import make_option
from django.utils.translation import ugettext_lazy, ugettext as _
from odk_logger.models import XForm
from odk_logger.models.instance import Instance

class Command(BaseCommand):
    help = ugettext_lazy('Repair submission counts for all users')

    def handle(self, *args, **kwargs):
        c = 0
        qs = XForm.objects.all()
        for form in qs:
            count = form.surveys.filter(is_deleted=False).count()
            new_num = count if count > 0 else -1
            if new_num != form.num_of_submissions:
                form.num_of_submissions = new_num
                form.save()
                c += 1
        print "Updated %d records." % c
