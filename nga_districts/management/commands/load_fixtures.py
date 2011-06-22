from django.core.management.base import BaseCommand
from django.core.management import call_command
import os
import json
from facilities.models import Facility, Variable, KeyRename, DataRecord
from facilities.facility_builder import FacilityBuilder
from utils.csv_reader import CsvReader
from django.conf import settings


class Command(BaseCommand):
    help = "Load the LGAs from fixtures."

    def handle(self, *args, **kwargs):
        self.drop_database()
        call_command('syncdb', interactive=False)
        self.print_stats()
        self.load_lgas()
        csvs = [
            (Variable, os.path.join('facilities', 'fixtures', 'variables.csv')),
            (KeyRename, os.path.join('facilities', 'fixtures', 'key_renames.csv')),
            ]
        for model, path in csvs:
            self.create_objects_from_csv(model, path)
        # self.load_surveys()
        facility_csvs = [
            ('Health', 'health.csv', os.path.join('data', 'health.csv')),
            ]
        for facility_type, data_source, path in facility_csvs:
            self.create_facilities_from_csv(facility_type, data_source, path)
        self.create_admin_user()
        self.print_stats()

    def drop_database(self):
        def drop_sqlite_database():
            try:
                os.remove('db.sqlite3')
                print 'removed db.sqlite3'
            except OSError:
                pass

        def drop_mysql_database():
            import MySQLdb
            db_name = settings.DATABASES['default']['NAME']
            db = MySQLdb.connect(
                "localhost",
                settings.DATABASES['default']['USER'],
                settings.DATABASES['default']['PASSWORD'],
                db_name
                )
            cursor = db.cursor()
            # to start up django the mysql database must exist
            cursor.execute("DROP DATABASE %s" % db_name)
            cursor.execute("CREATE DATABASE %s" % db_name)
            db.close()

        caller = {
            'django.db.backends.mysql': drop_mysql_database,
            'django.db.backends.sqlite3': drop_sqlite_database,
            }
        drop_function = caller[settings.DATABASES['default']['ENGINE']]
        drop_function()

    def print_stats(self):
        info = {
            'number of facilities': Facility.objects.count(),
            'facilities without lgas': Facility.objects.filter(lga=None).count(),
            'number of data records': DataRecord.objects.count(),
            }
        print json.dumps(info, indent=4)

    def load_lgas(self):
        for file_name in ['zone.json', 'state.json', 'lga.json']:
            call_command('loaddata', file_name)

    def create_objects_from_csv(self, model, path):
        csv_reader = CsvReader(path)
        for d in csv_reader.iter_dicts():
            model.objects.get_or_create(**d)

    def create_facilities_from_csv(self, facility_type, data_source, path):
        csv_reader = CsvReader(path)
        for d in csv_reader.iter_dicts():
            d['_data_source'] = data_source
            d['_facility_type'] = facility_type
            FacilityBuilder.create_facility_from_dict(d)

    def load_surveys(self):
        if not os.path.exists('xform_manager_dataset.json'):
            raise Exception("Download and unpack xform_manager_dataset.json into project dir.")
        call_command('loaddata', 'xform_manager_dataset.json')

    def create_admin_user(self):
        from django.contrib.auth.models import User
        admin, created = User.objects.get_or_create(
            username="admin",
            email="admin@admin.com",
            is_staff=True,
            is_superuser=True
            )
        admin.set_password("pass")
        admin.save()
