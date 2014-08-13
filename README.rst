Formhub
=======
.. image:: https://api.travis-ci.org/SEL-Columbia/formhub.png?branch=master
  :target: https://travis-ci.org/SEL-Columbia/formhub

Getting Started
---------------

* To build and install from source, follow the `Installation Guide <docs/install/README.md>`_

* Alternatively, you can just use these pre-built server images instead:

  * The public Formhub Amazon Machine Image (AMI) to `Run Your Own Formhub Instances on Amazon Web Services (AWS) <https://github.com/SEL-Columbia/formhub/wiki/How-To-Run-Your-Own-Formhub-Instances-on-Amazon-Web-Services>`_

  * The public Formhub Virtual Disk Image (VDI) to `Run Your Own Formhub Instances on VirtualBox <https://github.com/SEL-Columbia/formhub/wiki/How-To-Run-Your-Own-Formhub-Virtual-Machines-on-VirtualBox>`_

Contributing
------------

If you would like to contribute code please read
`Contributing Code to Formhub <https://github.com/SEL-Columbia/formhub/wiki/Contributing-Code-to-Formhub>`_.

Code Structure
--------------

Formhub is written in `Python <https://www.python.org/>`_, using the `Django Web Framework <https://www.djangoproject.com/>`_. 

In Django terms, an "app" is a bundle of Django code, including models and views, that lives together in a single Python package and represents a full Django application.

Formhub consists of three Django apps:

* odk_logger - This app serves XForms to ODK Collect and receives
  submissions from ODK Collect. This is a stand alone application.

* odk_viewer - This app provides a
  csv and xls export of the data stored in odk_logger. This app uses a
  data dictionary as produced by pyxform. It also provides a map and
  single survey view.

* main - This app is the glue that brings odk_logger and odk_viewer
  together.

Internationalization and Localization
-------------------------------------

Formhub can be presented in specific languages and formats, customized for specific audiences.

These examples were derived from `Django's Internationalization and Localization Documentation <https://docs.djangoproject.com/en/dev/topics/i18n/>`_ and there is also a good explanation in `The Django Book's Chapter on Internationalization <http://www.djangobook.com/en/2.0/chapter19.html>`_.

To generate a locale from scratch, e.g. Spanish:

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

