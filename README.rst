eHealth Africa
==============
this copy of the Formhub software is customized for the use and convenience of https://www.ehealthafrica.org
and our customers.  More complete documentation is found in the wiki at https://github.com/vernondcole/formhub/wiki

v v v v v v text below this point is unaltered from the original v v v v v v 

Formhub
=======

.. image:: https://api.travis-ci.org/SEL-Columbia/formhub.png?branch=master
  :target: https://travis-ci.org/SEL-Columbia/formhub

Installation
------------
Please read the `Installation and Deployment Guide <https://github.com/modilabs/formhub/wiki/Installation-and-Deployment>`_.

Contributing
------------

If you would like to contribute code please read
`Contributing Code to Formhub <https://github.com/eHealthAfrica/formhub/blob/develop/CONTRIBUTING.md>`_.

Code Structure
--------------

* odk_logger - This app serves XForms to ODK Collect and receives
  submissions from ODK Collect. This is a stand alone application.

* odk_viewer - This app provides a
  csv and xls export of the data stored in odk_logger. This app uses a
  data dictionary as produced by pyxform. It also provides a map and
  single survey view.

* main - This app is the glue that brings odk_logger and odk_viewer
  together.

Localization
------------

To generate a locale from scratch (ex. Spanish)

.. code-block:: sh

    $ django-admin.py makemessages -l es -e py,html,email,txt ;
    $ for app in {main,odk_viewer} ; do cd ${app} && django-admin.py makemessages -d djangojs -l es && cd - ; done

To update PO files

.. code-block:: sh

    $ django-admin.py makemessages -a ;
    $ for app in {main,odk_viewer} ; do cd ${app} && django-admin.py makemessages -d djangojs -a && cd - ; done

To compile MO files and update live translations

.. code-block:: sh

    $ django-admin.py compilemessages ;
    $ for app in {main,odk_viewer} ; do cd ${app} && django-admin.py compilemessages && cd - ; done

