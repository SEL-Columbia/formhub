NMIS Project v0.7
====================

How to get up & Running (with sample dataset and sqlite)
---------------------------------------------

0. Checkout this branch

    git fetch origin feature/dj13:feature/dj13 && git checkout feature/dj13

1. In a virtualenv, install requirements:

    pip install -r requirements.pip

2. Download the data into the "data" directory

    health.csv education.csv water.csv

3. Run load_fixtures management command

    python manage.py load_fixtures
