from django.core.management.base import BaseCommand
from django.core.management import call_command
import os
import json
from facilities.models import Facility, Variable, CalculatedVariable, \
    KeyRename, DataRecord
from facilities.facility_builder import FacilityBuilder
from utils.csv_reader import CsvReader
from django.conf import settings


class Command(BaseCommand):
    help = "Load the LGAs from fixtures."

    # python manage.py load_fixtures --limit will limit the import to
    # three lgas.
    from optparse import make_option
    option_list = BaseCommand.option_list + (
        make_option("--limit",
                    dest="limit_import",
                    default=False,
                    action="store_true"),
        )

    def handle(self, *args, **kwargs):
        self._limit_import = kwargs['limit_import']
        self.reset_database()
        self.load_lgas()
        self.load_key_renames()
        self.load_variables()
        self.load_table_defs()
        self.load_facilities()
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

    def reset_database(self):
        self.drop_database()
        call_command('syncdb', interactive=False)

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

    def load_key_renames(self):
        kwargs = {
            'model': KeyRename,
            'path': os.path.join('facilities', 'fixtures', 'key_renames.csv')
            }
        self.create_objects_from_csv(**kwargs)

    def create_objects_from_csv(self, model, path):
        csv_reader = CsvReader(path)
        for d in csv_reader.iter_dicts():
            model.objects.get_or_create(**d)

    def load_variables(self):
        def add_critical_variables():
            """
            I don't want to put these variables in fixtures because
            our code depends on their existence. We should think about
            where to put this code. Probably not in the load_fixtures
            script.
            """
            Variable.objects.get_or_create(data_type='string', slug='sector', name='Sector')
        add_critical_variables()

        csv_reader = CsvReader(os.path.join('facilities', 'fixtures', 'variables.csv'))
        for d in csv_reader.iter_dicts():
            # throw out the formula if it is empty
            if 'formula' in d and not d['formula']:
                del(d['formula'])
            if 'formula' in d:
                CalculatedVariable.objects.get_or_create(**d)
            else:
                Variable.objects.get_or_create(**d)

    def load_facilities(self):
        data_dir = 'data'
        sector_args = {
            'health': {
                'facility_type': 'Health',
                'data_source': 'health.csv',
                'path': os.path.join(data_dir, 'health.csv'),
                },
            'education': {
                'facility_type': 'Education',
                'data_source': 'education.csv',
                'path': os.path.join(data_dir, 'health.csv'),
                },
            'water': {
                'facility_type': 'Water',
                'data_source': 'water.csv',
                'path': os.path.join(data_dir, 'water.csv'),
                },
            }
        for sector in sector_args:
            self.create_facilities_from_csv(**sector_args[sector])

    def create_facilities_from_csv(self, facility_type, data_source, path):
        csv_reader = CsvReader(path)
        num_errors = 0
        for d in csv_reader.iter_dicts():
            if self._limit_import:
                if '_lga_id' not in d:
                    print d
                if d['_lga_id'] not in ['732', '127', '394']:
                    continue
            d['_data_source'] = data_source
            d['_facility_type'] = facility_type
            d['sector'] = facility_type
            FacilityBuilder.create_facility_from_dict(d)
            # try:
            #     FacilityBuilder.create_facility_from_dict(d)
            # except:
            #     num_errors += 1
        print "Had %d error(s) when importing %s facilities..." % (num_errors, facility_type)

    def load_table_defs(self):
        table_types = [
            ("Health", "health"),
            ("Education", "education"),
            ("Water", "water")
            ]
        from facility_views.models import FacilityTable
        for name, slug in table_types:
            curtable = FacilityTable.objects.create(name=name, slug=slug)
            csv_reader = CsvReader(os.path.join("facility_views","table_defs", "%s.csv" % slug))
            for d in csv_reader.iter_dicts():
                curtable.add_variable(d)

    def load_surveys(self):
        xfm_json_path = os.path.join('data','xform_manager_dataset.json')
        if not os.path.exists(xfm_json_path):
            raise Exception("Download and unpack xform_manager_dataset.json into project's data dir.")
        call_command('loaddata', xfm_json_path)

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
