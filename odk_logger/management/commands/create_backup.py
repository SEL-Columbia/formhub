import os
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext_lazy, ugettext as _
from django.contrib.auth.models import User

from onadata.apps.logger.models import XForm
from onadata.libs.utils.backup_tools import create_zip_backup


class Command(BaseCommand):
    args = "outfile username [id_string]"
    help = "Create a zip backup of a form and all its submissions."

    def handle(self, *args, **options):
        try:
            output_file = args[0]
        except IndexError:
            raise CommandError(_("Provide the path to the zip file to backup"
                                 " to"))
        else:
            output_file = os.path.realpath(output_file)

        try:
            username = args[1]
        except IndexError:
            raise CommandError(_("You must provide the username to publish the"
                                 " form to."))
        # make sure user exists
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(_("The user '%s' does not exist.") % username)

        try:
            id_string = args[2]
        except IndexError:
            xform = None
        else:
            # make sure xform exists
            try:
                xform = XForm.objects.get(user=user, id_string=id_string)
            except XForm.DoesNotExist:
                raise CommandError(_("The id_string '%s' does not exist.") %
                                   id_string)
        create_zip_backup(output_file, user, xform)
