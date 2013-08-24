#!/usr/bin/env python
# encoding=utf-8
from __future__ import print_function
import os
import sys


if __name__ == "__main__":
    # altered by Vernon Cole for new settings layout
    try:
        print('Your environment is:"{}"'.format(os.environ['DJANGO_SETTINGS_MODULE']))
    except KeyError:
        print('**Note: you are using EXAMPLE SETTINGS (by default.)')
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "formhub.settings.example")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
