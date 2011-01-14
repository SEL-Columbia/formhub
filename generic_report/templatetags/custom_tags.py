#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

from django.template import  Library

register = Library()

def pourcent(a, b, format='%d'):
    """
        Return the pourcentage of value 'a' in relation to value b.
    """
    return format % (float(a) * 100 / float(b))

paginator_number = register.simple_tag(pourcent)
