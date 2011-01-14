#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

class ViewNameMiddleware(object):  
    """
        Add the view name in the request
    """
    def process_view(self, request, view_func, view_args, view_kwargs):  
        request.view_name = ".".join((view_func.__module__, view_func.__name__))  
  
