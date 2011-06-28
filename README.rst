NMIS Project v0.7
====================

1. Checkout this branch

    git checkout feature/dj13

2. Install MySQL. Right now we put MySQL-python in the
requirements.pip file. This makes deployment easier, but means you
have to have MySQL installed on your machine to install the
requirements.

    sudo apt-get install mysql-server mysql-client libmysqlclient-dev

3. Change directory into the folder where you want to make your
virtual environment, and make a new virtualenv with the following
command

    virtualenv --no-site-packages [name-of-new-virtualenv]

Activate the virtual environment

    source [path-to-virtualev-dir]/bin/activate

Change directory into the folder containing this README.rst and
install the requirements

    pip install -r requirements.pip

4. Install dropbox and make a symbolic link to the cleaned csv folder

    ln -s ~/Dropbox/NMIS\ -\ Nigeria/NMIS\ Data/final_cleaned_data/csv/facility/ data

5. Run load_fixtures management command

    python manage.py load_fixtures
