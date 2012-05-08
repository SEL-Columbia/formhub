Installation
============

Here are the steps I went through to install formhub in Ubuntu
10.04. First, I set up a new virtual environment:

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

    pip install -r requirements.pip

Install Mongodb:

    sudo apt-key adv --keyserver keyserver.ubuntu.com --recv 7F0CEB10

    Add this line to /etc/apt/sources.list then save:
    deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen

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

Running Tests and Contributing
==============================

To run all tests enter the following:

    python manage.py test

To run the tests for a specific app, e.g. main, enter:

    python manage.py test main

To run the test for a specific class in a specific app, e.g. the class ``TestFormErrors`` in main, enter:

    python manage.py test main.TestFormErrors

To run the test for a specific method in a specific class in a specific app, e.g. the method ``test_submission_deactivated`` in the class ``TestFormErrors`` in main, enter:

    python manage.py test main.TestFormErrors.test_submission_deactivated

If you would like to contribute code please read:

https://github.com/modilabs/formhub/wiki/Contributing-Code-to-Formhub

Code Structure
==============

* odk_logger - This app serves XForms to ODK Collect and receives
  submissions from ODK Collect. This is a stand alone application.

* odk_viewer - This app provides a
  csv and xls export of the data stored in odk_logger. This app uses a
  data dictionary as produced by pyxform. It also provides a map and
  single survey view.

* main - This app is the glue that brings odk_logger and odk_viewer
  together.

In general, I think breaking these pieces into separate applications
has been a mistake. I think we should move to having all of the code
for formhub in a single Django application.
