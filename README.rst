Formhub
=======

.. image:: https://secure.travis-ci.org/modilabs/formhub.png?branch=master
  :target: http://travis-ci.org/modilabs/formhub

Installation
------------

Ubuntu 12.04
^^^^^^^^^^^^

Install system libraries and start services:

    # apt-get update

    # apt-get upgrade

    # apt-get install default-jre gcc git mongodb python-dev python-virtualenv libjpeg-dev libfreetype6-dev zlib1g-dev

    # start mongodb

Make directory structure and Clone formhub:

    $ mkdir -p src/formhub-app

    $ cd src/formhub-app

    $ git clone git://github.com/modilabs/formhub.git

Make virtual environment and install requirements:

    $ virtualenv --no-site-packages project_env

    $ source project_env/bin/activate

    $ cd formhub

(NB: there is a known bug that prevents numpy from installing correctly when in requirements.pip file)

    $ pip install numpy
(NB: PIL under virtualenv usually does not have some codecs compiled| to make sure jpeg codec is included)

    $ sudo ln -s /usr/lib/x86_64-linux-gnu/libfreetype.so /usr/lib/

    $ sudo ln -s /usr/lib/x86_64-linux-gnu/libz.so /usr/lib/

    $ sudo ln -s /usr/lib/x86_64-linux-gnu/libjpeg.so /usr/lib/

    $ pip install -r requirements.pip

(OPTIONAL) For MySQL, s3, ses:

    # apt-get install libmysqlclient-dev mysql-server

    $ pip install -r requirements-mysql.pip

    $ pip install -r requirements-s3.pip

    $ pip install -r requirements-ses.pip

Create a database and start server:

    create or update your local-settings.py file

    $ python manage.py syncdb

    $ python manage.py migrate

    $ python manage.py runserver

(OPTIONAL) Apache and system administration tools:

    # apt-get install apache libapache2-mode-wsgi

    # apt-get install htop monit

    set up apache and monit

Ubuntu 10.04
^^^^^^^^^^^^

First, I set up a new virtual environment:

    sudo apt-get install python-virtualenv

    cd ~/Documents

    mkdir virtual_environments

    cd virtual_environments

    virtualenv --no-site-packages formhub

    source formhub/bin/activate

Second, I cloned the repo:

    cd ~/Documents

    git clone git@github.com:modilabs/formhub.git

Install the requirements:

    cd formhub

    pip install numpy --use-mirrors

    pip install -r requirements.pip

Install Mongodb:

    sudo apt-key adv --keyserver keyserver.ubuntu.com --recv 7F0CEB10

    echo 'deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen' >> /etc/apt/sources.list

    sudo apt-get update
    
    sudo apt-get install mongodb-10gen

If you don't already have a Java Runtime Environment installed this is
necessary for running ODK Validate. A *.jar file used to validate
XForms.

    sudo apt-get install default-jre

To create a database for your development server do the following:

    python manage.py syncdb

    python manage.py migrate

And now you should be ready to run the server:

    python manage.py runserver

Running Tests
-------------

To run all tests enter the following:

    python manage.py test

To run the tests for a specific app, e.g. main, enter:

    python manage.py test main

To run the test for a specific class in a specific app, e.g. the class ``TestFormErrors`` in main, enter:

    python manage.py test main.TestFormErrors

To run the test for a specific method in a specific class in a specific app, e.g. the method ``test_submission_deactivated`` in the class ``TestFormErrors`` in main, enter:

    python manage.py test main.TestFormErrors.test_submission_deactivated

To run javascript tests enter the following, NOTE that the testDir and configFile paths are relative to the js_tests/EnvJasmine directory:

    ./js_tests/EnvJasmine/bin/run_all_tests.sh --testDir=../ --configFile=../env_jasmine.conf.js

Deploying
---------

To deploy you will need Fabric:

    pip install fabric

You will need the appopriate .pem file in order to deploy to AWS. You will need
to edit fabfile.py if you want to customize the deployments.

To deploy master to the production server:

    fab deploy:prod

To deploy master to the development server:

    fab deploy:dev

To deploy a specific branch to the development server:

    fab deploy:dev,branch=[BRANCH NAME]

Contributing
------------

If you would like to contribute code please read:

https://github.com/modilabs/formhub/wiki/Contributing-Code-to-Formhub

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

    django-admin.py makemessages -l es -e py,html,email,txt ;
    for app in {main,odk_viewer} ; do cd ${app} && django-admin.py makemessages -d djangojs -l es && cd - ; done

To update PO files

    django-admin.py makemessages -a ;
    for app in {main,odk_viewer} ; do cd ${app} && django-admin.py makemessages -d djangojs -a && cd - ; done

To compile MO files and update live translations

    django-admin.py compilemessages ;
    for app in {main,odk_viewer} ; do cd ${app} && django-admin.py compilemessages && cd - ; done
