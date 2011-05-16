NMIS Project v0.5
=================

Installation
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

    $ pip install -r requirements.txt

7. Copy example settings and edit them appropriately

    $ cp custom_settings_example.py custom_settings.py

8. Clone the XForm Manager inside this Django project:

    $ git clone https://github.com/mvpdev/xform_manager.git
