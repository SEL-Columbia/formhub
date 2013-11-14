#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import os, glob
from optparse import make_option
from django.core.management.base import BaseCommand
from django.utils.translation import ugettext_lazy
from odk_logger.models.xform import XForm
from django.contrib.auth.models import User
from odk_logger.models.instance import get_id_string_from_xml_str


class Command(BaseCommand):
    help = ugettext_lazy("Import a folder of xml forms for ODK.  Arguments-> forder.name  username")

    option_list = BaseCommand.option_list + (
        make_option('-r', '--replace',
            action='store_true',
            dest='replace',
            help=ugettext_lazy("Replace existing form if any")),
        )

    def handle(self, *args, **kwargs):
        path = args[0]

        try:
            username = args[1]
        except IndexError:
            raise CommandError(_("You must provide the username to publish the form to."))
        # make sure user exists
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(_("The user '%s' does not exist.") % username)

        for form in glob.glob( os.path.join(path, "*") ):
            f = open(form)
            xml = f.read()
            id_string = get_id_string_from_xml_str(xml)

            # check if a form with this id_string exists for this user
            form_already_exists = XForm.objects.filter(user=user,
                id_string=id_string).count() > 0

            if form_already_exists:
                if options.has_key('replace') and options['replace']:
                    XForm.objects.filter(user=user,id_string=id_string).delete()

            XForm.objects.get_or_create(xml=xml, downloadable=False, user=user, id_string=id_string)
            f.close()
