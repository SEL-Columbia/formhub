import os
import sys
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext_lazy, ugettext as _
from django.contrib.auth.models import User
from utils.backup_tools import restore_backup_from_zip


class Command(BaseCommand):
    args = 'username input_file'
    help = ugettext_lazy("Restore a zip backup of a form and all its"
                         " submissions")

    def handle(self, *args, **options):
        try:
            username = args[0]
        except IndexError:
            raise CommandError(_("You must provide the username to publish the"
                                 " form to."))
            # make sure user exists
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(_("The user '%s' does not exist.") % username)

        try:
            input_file = args[1]
        except IndexError:
            raise CommandError(_("You must provide the path to restore from."))
        else:
            input_file = os.path.realpath(input_file)

        num_instances, num_restored = restore_backup_from_zip(
            input_file, username)
        sys.stdout.write("Restored %d of %d submissions\n" %
                         (num_restored, num_instances))