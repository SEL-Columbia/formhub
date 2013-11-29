"""
Restore Xform submission counter counter to agree with actual number of submissions in the database
"""
from django.core.management.base import BaseCommand
from django.utils.translation import ugettext_lazy
from odk_logger.models import XForm

class Command(BaseCommand):
    help = ugettext_lazy('Reset submission count to actual sql instances')

    def handle(self, *args, **kwargs):
        c = 0
        for form in XForm.objects.all():
            count = form.surveys.filter(is_deleted=False).count()
            if count <= 0:
                count = -1;
            if form.num_of_submissions != count:
                form.num_of_submissions = count
                form.save()
                c += 1
        print "Updated %d records." % c
