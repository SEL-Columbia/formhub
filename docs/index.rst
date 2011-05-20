NMIS Project Documentation
==========================

The objective of this project is to receive and display survey data
from ODK Collect.

The key apps in this Django project are:

* :doc:`pyxform` is a Python library designed to make writing XForms for ODK
  Collect easy. It also provides a nice Python API for displaying data
  collected using XForms.

* xform_manager is a pluggable Django app that serves XForms and logs
  submissions. This is a great app if you want to add support for ODK
  Collect in your Django project.

* parsed_xforms is the glue that holds all the other Django apps
  together.

Contents
========

.. toctree::
   :maxdepth: 2

   pyxform

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
