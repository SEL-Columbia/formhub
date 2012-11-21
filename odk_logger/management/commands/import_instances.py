#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
import os
import glob
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.translation import ugettext as _, ugettext_lazy
from odk_logger. import_tools import django_file, import_instances_from_zip, import_instances_from_path

class Command(BaseCommand):
    args = 'username path'
    help = ugettext_lazy("Import a zip file, a directory containing zip files or a directory of ODK instances")

    def handle(self, *args, **kwargs):
        if len(args) < 2:
            raise CommandError(_("Usage: <command> username file/path."))
        username = args[0]
        path = args[1]
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(_("The specified user '%s' does not exist.") % username)

        # make sure path exists
        if not os.path.exists(path):
            raise CommandError(_("The specified path '%s' does not exist.") % path)

        for dir, subdirs, files in os.walk(path):
            # check if the dir has an odk directory
            if "odk" in subdirs:
                # dont walk further down this dir
                subdirs.remove("odk")
                self.stdout.write(_("Importing from dir %s..\n") % dir)
                (total_count, success_count, errors) = import_instances_from_path(dir, user)
                self.stdout.write(_("Total: %d, Imported: %d, Errors: %s\n------------------------------\n") % (total_count, success_count, errors))
            for file in files:
                filepath = os.path.join(path, file)
                if os.path.isfile(filepath) and os.path.splitext(filepath)[1].lower() == ".zip":
                    self.stdout.write(_("Importing from zip at %s..\n") % filepath)
                    (total_count, success_count, errors) = import_instances_from_zip(filepath, user)
                    self.stdout.write(_("Total: %d, Imported: %d, Errors: %s\n------------------------------\n") % (total_count, success_count, errors))