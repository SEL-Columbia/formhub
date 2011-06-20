NMIS Project v0.7
====================

How to get up & Running (with sample dataset and sqlite)
---------------------------------------------

1. In a virtualenv, install requirements:

    pip install -r requirements.pip


2. Download xform_manager_dataset.json into the project directory


3. Run load_fixtures management command

    python manage.py load_fixtures


Installation (old)
------------
1. Install virtualenv, and mongodb if needed

    $ sudo apt-get install python-virtualenv mongodb

2. Create a virtual environment

    $ virtualenv --no-site-packages nmis_env

3. Activate the virtual environment

    $ source nmis_env/bin/activate

4. Clone this git repository

    $ git clone https://github.com/mvpdev/nmis.git

5. Before installing fabric I had to install header files for Python:

    $ sudo apt-get install python-dev

6. Install all the requirements including fabric

    $ pip install -r requirements.pip

7. Copy example settings and edit them appropriately

    $ cp custom_settings_example.py custom_settings.py

8. Clone the XForm Manager inside this Django project:

    $ git clone https://github.com/mvpdev/xform_manager.git

For those installing MySQL we had to do the following:

    sudo apt-get install mysql-server mysql-client libmysqlclient-dev
    pip install MySQL-python
