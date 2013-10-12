Formhub
=======

.. image:: https://secure.travis-ci.org/modilabs/formhub.png?branch=master
  :target: http://travis-ci.org/modilabs/formhub

Installation
------------

Install system libraries and start services:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: sh

    $ sudo apt-get update
    $ sudo apt-get upgrade
    $ sudo apt-get install default-jre gcc git python-dev python-virtualenv libjpeg-dev libfreetype6-dev zlib1g-dev rabbitmq-server

Install Mongodb:
^^^^^^^^^^^^^^^^

Ubuntu 12.04

.. code-block:: sh

    $ sudo apt-get install mongodb
    $ sudo start mongodb

Ubuntu 10.04

.. code-block:: sh

    $ sudo apt-key adv --keyserver keyserver.ubuntu.com --recv 7F0CEB10
    $ sudo echo 'deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen' >> /etc/apt/sources.list
    $ sudo apt-get update
    $ sudo apt-get install mongodb-10gen


Set up a new virtual environment:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: sh

    $ mkdir ~/virtual_environments
    $ cd ~/virtual_environments
    $ virtualenv --no-site-packages formhub
    $ source formhub/bin/activate

Make directory structure and clone formhub:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: sh

    $ mkdir -p ~/src/formhub-app
    $ cd ~/src/formhub-app
    $ git clone git://github.com/modilabs/formhub.git
    $ git submodule init
    $ git submodule update

Install requirements:
^^^^^^^^^^^^^^^^^^^^^

(NB: there is a known bug that prevents numpy from installing correctly when in requirements.pip file)

.. code-block:: sh

    $ pip install numpy  --use-mirrors
    $ pip install -r requirements.pip

(NB: PIL under virtualenv usually does not have some codecs compiled| to make sure jpeg codec is included)

.. code-block:: sh

    $ sudo ln -s /usr/lib/x86_64-linux-gnu/libfreetype.so /usr/lib/
    $ sudo ln -s /usr/lib/x86_64-linux-gnu/libz.so /usr/lib/
    $ sudo ln -s /usr/lib/x86_64-linux-gnu/libjpeg.so /usr/lib/
    $ pip install -r requirements.pip

(OPTIONAL) For MySQL, s3, ses:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: sh

    # apt-get install libmysqlclient-dev mysql-server
    $ pip install -r requirements-mysql.pip

NOTE: If you inted to use special characters from other languages within your forms, or are unsure if you will, you shoud ensure your databse uses the utf-8 characterset by default e.g. for mysql

.. code-block:: sh

    $ mysql> CREATE DATABASE formhub CHARACTER SET utf8;
    $ pip install -r requirements-s3.pip
    $ pip install -r requirements-ses.pip

Create a database and start server:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    update your preset/default_settings.py file,
    or create a new preset and
      modify manage.py to import it,
      or define the environment variable DJANGO_SETTINGS_MODULE to specify it.

.. code-block:: sh

    $ python manage.py syncdb --noinput
    $ python manage.py migrate


    optional: create a super user

.. code-block:: sh

    $ python manage.py createsuperuser

Configure the celery daemon:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Copy the required files from the extras directory:

.. code-block:: sh

    $ sudo cp ~/src/formhub-app/formhub/extras/celeryd/etc/init.d/celeryd /etc/init.d/celeryd
    $ sudo cp ~/src/formhub-app/formhub/extras/celeryd/etc/default/celeryd /etc/default/celeryd

Open /etc/default/celeryd and update the path to your formhub install directory, if you directory structure is identical to what is described above, you only need to update your username.

Start the celery daemon

.. code-block:: sh

    $ sudo /etc/init.d/celeryd start

(OPTIONAL) Apache and system administration tools:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: sh

    $ sudo apt-get install apache libapache2-mode-wsgi
    $ sudo apt-get install htop monit

And now you should be ready to run the server:

.. code-block:: sh

    $ python manage.py runserver

Running Tests
-------------

To run all tests enter the following:

.. code-block:: sh

    $ python manage.py test

To run the tests for a specific app, e.g. main, enter:

.. code-block:: sh

    $ python manage.py test main

To run the test for a specific class in a specific app, e.g. the class ``TestFormErrors`` in main, enter:

.. code-block:: sh

    python manage.py test main.TestFormErrors

To run the test for a specific method in a specific class in a specific app, e.g. the method ``test_submission_deactivated`` in the class ``TestFormErrors`` in main, enter:

.. code-block:: sh

    $ python manage.py test main.TestFormErrors.test_submission_deactivated

To run javascript tests enter the following, NOTE that the testDir and configFile paths are relative to the js_tests/EnvJasmine directory:

.. code-block:: sh

    $ ./js_tests/EnvJasmine/bin/run_all_tests.sh --testDir=../ --configFile=../env_jasmine.conf.js

(OPTIONAL) Re-compiling the less css files
---------------------------------------

Install nodejs
^^^^^^^^^^^^^^

.. code-block:: sh

    $ sudo apt-get install python g++ make
    $ mkdir ~/nodejs && cd $_
    $ wget -N http://nodejs.org/dist/node-latest.tar.gz
    $ tar xzvf node-latest.tar.gz && cd `ls -rd node-v*`
    $ ./configure
    $ sudo make install

Install recess, uglifyjs and less via npm (Node Package Manager)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: sh

    $ sudo npm install -g recess
    $ sudo npm install -g uglifyjs
    $ sudo npm install -g less

Compile the less files
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: sh

    $ cd ~/src/formhub-app/formhub/main/static/bootstrap
    $ make

Deploying
---------

To deploy you will need Fabric:

.. code-block:: sh

    $ pip install fabric

You will need the appopriate .pem file in order to deploy to AWS. You will need
to edit fabfile.py if you want to customize the deployments.

To deploy master to the production server:

.. code-block:: sh

    $ fab deploy:prod

To deploy master to the development server:

.. code-block:: sh

    $ fab deploy:dev

To deploy a specific branch to the development server:

.. code-block:: sh

    $ fab deploy:dev,branch=[BRANCH NAME]

Contributing
------------

If you would like to contribute code please read
`Contributing Code to Formhub <https://github.com/modilabs/formhub/wiki/Contributing-Code-to-Formhub>`_.

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
