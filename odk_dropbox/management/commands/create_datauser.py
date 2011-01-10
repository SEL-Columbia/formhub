#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User, Permission

class Command(BaseCommand):
    help = "Set up the readdata user and the read all data permission"

    def handle(self, *args, **kwargs):
        username = "readdata"
        u, created = User.objects.get_or_create(username=username)
        u.set_password("bcb8487c84")
        u.save()

        read_all_data, created = Permission.objects.get_or_create(
            name = "Can read all data",
            content_type = ContentType.objects.get_for_model(Permission),
            codename = "read_all_data"
            )
        if not u.has_perm(read_all_data):
            u.user_permissions.add(read_all_data)
