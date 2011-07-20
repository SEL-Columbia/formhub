from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db.models import Count
import os
import json
import time
import sys
from collections import defaultdict
from facilities.models import Facility, Variable, CalculatedVariable, \
    KeyRename, FacilityRecord, Sector, FacilityType, PartitionVariable, \
    LGAIndicator, GapVariable
from nga_districts.models import LGA, LGARecord
from facilities.facility_builder import FacilityBuilder
from utils.csv_reader import CsvReader
from django.conf import settings
from optparse import make_option


class Command(BaseCommand):
    help = "Load the LGA data from fixtures."

    option_list = BaseCommand.option_list + (
        make_option("-l", "--limit",
                    dest="limit_import",
                    default=False,
                    help="Limit the imported LGAs to the list specified in settings.py",
                    action="store_true"),
        make_option("-d", "--debug",
                    dest="debug",
                    help="print debug stats about the query times.",
                    default=False,
                    action="store_true"),
        )

    limit_lgas = settings.LIMITED_LGA_LIST

    def handle(self, *args, **kwargs):
        self._limit_import = kwargs['limit_import']
        self._debug = kwargs['debug']
        self._start_time = time.time()
        self.reset_database()
        self.load_lgas()
        self.create_sectors()
        self.create_facility_types()
        self.load_key_renames()
        self.load_variables()
        self.load_table_defs()
        self.load_facilities()
        self.load_lga_data()
        call_command("calculate_lga_indicators")
        self.create_admin_user()
        self._end_time = time.time()
        self.print_stats()

    def drop_database(self):
        db_host = settings.DATABASES['default']['HOST'] or 'localhost'
        db_name = settings.DATABASES['default']['NAME']
        db_user = settings.DATABASES['default']['USER']
        db_password = settings.DATABASES['default']['PASSWORD']

        def drop_sqlite_database():
            try:
                os.remove('db.sqlite3')
                print 'removed db.sqlite3'
            except OSError:
                pass

        def drop_mysql_database():
            import MySQLdb
            conn = MySQLdb.connect(
                db_host,
                db_user,
                db_password,
                db_name
            )
            cursor = conn.cursor()
            # to start up django the mysql database must exist
            cursor.execute("DROP DATABASE %s" % db_name)
            cursor.execute("CREATE DATABASE %s" % db_name)
            conn.close()

        def drop_postgresql_database():
            import psycopg2
            # connect to postgres db to drop and recreate db
            conn = psycopg2.connect(
                database='postgres',
                user=db_user,
                host=db_host,
                password=db_password
            )
            conn.set_isolation_level(
                psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            cursor.execute("DROP DATABASE %s" % db_name)
            cursor.execute("CREATE DATABASE %s" % db_name)
            conn.close()

        caller = {
            'django.db.backends.mysql': drop_mysql_database,
            'django.db.backends.sqlite3': drop_sqlite_database,
            'django.db.backends.postgresql_psycopg2': drop_postgresql_database,
            }
        drop_function = caller[settings.DATABASES['default']['ENGINE']]
        drop_function()

    def reset_database(self):
        self.drop_database()
        call_command('syncdb', interactive=False)

    def print_stats(self):
        def seconds_to_hms(seconds):
            return time.strftime('%H:%M:%S', time.gmtime(seconds))

        def get_variable_usage():
            record_types = [FacilityRecord, LGARecord]
            totals = defaultdict(int)
            for record_type in record_types:
                counts = record_type.objects.values('variable').annotate(Count('variable'))
                for d in counts:
                    totals[d['variable']] += d['variable__count']
            return totals

        def get_unused_variables():
            all_vars = set([x.slug for x in Variable.objects.all()])
            used_vars = set(get_variable_usage().keys())
            return sorted(list(all_vars - used_vars))

        info = {
            'number of facilities': Facility.objects.count(),
            'facilities without lgas': Facility.objects.filter(lga=None).count(),
            'number of facility records': FacilityRecord.objects.count(),
            'number of lga records': LGARecord.objects.count(),
            'time': seconds_to_hms(self._end_time - self._start_time),
            'unused variables': get_unused_variables(),
            }
        print json.dumps(info, indent=4)

        from django.db import connection
        if self._debug:
            for query in connection.queries:
                if float(query['time']) > .01:
                    print query

    def load_lgas(self):
        for file_name in ['zone.json', 'state.json', 'lga.json']:
            call_command('loaddata', file_name)

    def create_sectors(self):
        sectors = ['Education', 'Health', 'Water']
        for sector in sectors:
            Sector.objects.get_or_create(slug=sector.lower(), name=sector)

    def create_facility_types(self):
        get = lambda node_id: FacilityType.objects.get(pk=node_id)
        facility_types = [
                (('health', 'Health'), [
                    (('level_1', 'Level 1'), [
                        (('healthpost', 'Health Post'), []),
                        (('dispensary', 'Dispensary'), []),
                    ]),
                    (('level_2', 'Level 2'), [
                        (('primaryhealthclinic', 'Primary Health Clinic'), []),
                    ]),
                    (('level_3', 'Level 3'), [
                        (('primaryhealthcarecentre', 'Primary Health Care Centre'), []),
                        (('comprehensivehealthcentre', 'Comprehensive Health Centre'), []),
                        (('wardmodelprimaryhealthcarecentre', 'Ward Model Primary Health Care Centre'), []),
                        (('maternity', 'Maternity'), []),
                    ]),
                    (('level_4', 'Level 4'), [
                        (('cottagehospital', 'Cottage Hospital'), []),
                        (('generalhospital', 'General Hospital'), []),
                        (('specialisthospital', 'Specialist Hospital'), []),
                        (('teachinghospital', 'Teaching Hospital'), []),
                        (('federalmedicalcare', 'Federal Medical Care'), []),
                    ]),
                    (('other', 'Other'), [
                        (('private', 'Private'), []),
                        (('other', 'Other'), []),
                    ]),
                ]),
                (('education', 'Education'), []),
                (('water', 'Water'), []),
            ]

        def add(child, parent):
            slug = child[0][0]
            name = child[0][1]
            grandchildren = child[1]
            child = parent.add_child(slug=slug, name=name)
            for grandchild in grandchildren:
                add(grandchild, child)

        root = FacilityType.add_root(slug='facility_type', name='Facility Type')
        for facility_type in facility_types:
            add(facility_type, root)

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
        """
        Load variables runs through variables.csv and populates these models
          * Variable
          * CalculatedVariable
          * LGAIndicator
          * GapVariable
        """

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

        def add_variable_from_dict(d):
            """
            Adds the variable described by the data in d.
            """
            if 'data_type' not in d or 'SECTION' in d or 'COMMENTS' in d:
                # this row does not define a new variable
                pass
            elif 'formula' in d:
                CalculatedVariable.objects.get_or_create(**d)
            elif 'partition' in d:
                PartitionVariable.objects.get_or_create(**d)
            elif 'origin' in d and 'method' in d and 'sector' in d:
                d['origin'] = Variable.objects.get(slug=d['origin'])
                d['sector'] = Sector.objects.get(slug=d['sector'])
                lga_indicator, created = LGAIndicator.objects.get_or_create(**d)
            elif 'variable' in d and 'target' in d:
                d['variable'] = Variable.objects.get(slug=d['variable'])
                d['target'] = Variable.objects.get(slug=d['target'])
                gap_analyzer, created = GapVariable.objects.get_or_create(**d)
            else:
                Variable.objects.get_or_create(**d)

        for d in csv_reader.iter_dicts():
            if self._debug:
                add_variable_from_dict(d)
            else:
                try:
                    add_variable_from_dict(d)
                except:
                    raise Exception("Variable import failed for data: %s" % d)

    def load_facilities(self):
        sectors = [
            {
                'sector': 'Health',
                'data_source': 'health.csv',
                },
            {
                'sector': 'Education',
                'data_source': 'education.csv',
                },
            {
                'sector': 'Water',
                'data_source': 'water.csv',
                },
            {
                'sector': 'Health',
                'data_source': 'Health_2011_05_02.csv',
                },
            {
                'sector': 'Education',
                'data_source': 'Education_2011_05_02.csv',
                },
            {
                'sector': 'Water',
                'data_source': 'Water_2011_05_02.csv',
                },

            ]
        for sector in sectors:
            self.create_facilities_from_csv(**sector)

    def create_facilities_from_csv(self, sector, data_source):
        data_dir = 'data/facility'
        path = os.path.join(data_dir, data_source)
        csv_reader = CsvReader(path)

        for d in csv_reader.iter_dicts():
            if self._limit_import:
                if '_lga_id' not in d:
                    print d
                if d['_lga_id'] not in self.limit_lgas:
                    continue
            d['_data_source'] = data_source
            d['_facility_type'] = sector.lower()
            d['sector'] = sector
            facility = FacilityBuilder.create_facility_from_dict(d)

    def load_lga_data(self):
        data_dir = 'data/lga'
        data_args = {
            'population': {
                'data': 'population',
                'path': os.path.join(data_dir, 'population.csv'),
                'data_format': 'variable_ids_in_cols',
                },
            'area': {
                'data': 'area',
                'path': os.path.join(data_dir, 'area.csv'),
                'data_format': 'variable_ids_in_cols',
                },
            'health': {
                'data': 'health',
                'path': os.path.join(data_dir, 'health.csv'),
                'data_format': 'variable_ids_in_rows',
                },
            'education': {
                'data': 'education',
                'path': os.path.join(data_dir, 'education.csv'),
                'data_format': 'variable_ids_in_rows',
                },
            'infrastructure': {
                'data': 'infrastructure',
                'path': os.path.join(data_dir, 'infrastructure.csv'),
                'data_format': 'variable_ids_in_rows',
                },
            }
        for kwargs in data_args:
            self.load_lga_data_from_csv(**data_args[kwargs])

    def load_lga_data_from_csv(self, data, path, data_format):
        csv_reader = CsvReader(path)
        num_errors = 0
        for d in csv_reader.iter_dicts():
            if self._limit_import:
                if '_lga_id' not in d:
                    print d
                if d['_lga_id'] not in self.limit_lgas:
                    continue
            lga = LGA.objects.get(id=d['_lga_id'])
            # if the variable_id is in the row grab it along
            # with the value and put it in the dict
            if data_format == 'variable_ids_in_rows':
                d = {d['slug']: d['value']}
            if self._debug:
                lga.add_data_from_dict(d)
            else:
                try:
                    lga.add_data_from_dict(d)
                except KeyboardInterrupt:
                    sys.exit(0)
                except:
                    num_errors += 1
        if not self._debug:
            print "Had %d error(s) when importing LGA %s data..." % (num_errors, data)

    def load_table_defs(self):
        """
        Table defs contain details to help display the data. (table columns, etc)
        """
        call_command('load_table_defs')

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
        mdg_user, created = User.objects.get_or_create(
            username="mdg",
            email="mdg@example.com",
            is_staff=True,
            is_superuser=True
            )
        mdg_user.set_password("2015")
        mdg_user.save()
