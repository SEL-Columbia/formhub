#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

import datetime
from haystack.indexes import *
from haystack import site

from odk_dropbox.models import Phone

site.register(Phone)
