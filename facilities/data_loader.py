from django.core.management import call_command
from django.db.models import Count
import os
import json
from collections import defaultdict
from facilities.models import Facility, Variable, CalculatedVariable, \
    KeyRename, FacilityRecord, Sector, FacilityType, PartitionVariable, \
    LGAIndicator, GapVariable
from nga_districts.models import LGA, LGARecord
from facilities.facility_builder import FacilityBuilder
from utils.csv_reader import CsvReader
from utils.timing import print_time
from django.conf import settings


class DataLoader(object):

    limit_lgas = settings.LIMITED_LGA_LIST

    def __init__(self, **kwargs):
        self._limit_import = kwargs.get('limit_import', False)
        self._debug = kwargs.get('debug', False)
        self._data_dir = kwargs.get('data_dir', 'data')

    def setup(self):
        self.reset_database()
        self.load()
        self.print_stats()

    def load(self):
        self.load_system()
        self.load_data()
        self.load_calculations()

    @print_time
    def reset_database(self):
        self._drop_database()
        call_command('syncdb', interactive=False)

    def load_system(self):
        self.create_users()
        self.create_sectors()
        self.create_facility_types()
        self.load_key_renames()
        self.load_variables()
        self.load_table_defs()

    def load_data(self):
        self.load_facilities()
        self.load_lga_data()

    def load_calculations(self):
        self.calculate_lga_indicators()
        self.calculate_lga_gaps()

    @print_time
    def create_users(self):
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

    @print_time
    def create_sectors(self):
        sectors = ['Education', 'Health', 'Water']
        for sector in sectors:
            Sector.objects.get_or_create(slug=sector.lower(), name=sector)

    @print_time
    def create_facility_types(self):
        get = lambda node_id: FacilityType.objects.get(pk=node_id)
        facility_types = {
            'slug': 'facility',
            'name': 'Facility',
            'children': [
                {
                    'slug': 'education',
                    'name': 'Education',
                    'children': [],
                    },
                {
                    'slug': 'water',
                    'name': 'Water',
                    'children': [],
                    },
                {
                    'slug': 'health',
                    'name': 'Health',
                    'children': [
                        {
                            'slug': 'level_1',
                            'name': 'Level 1',
                            'children': [
                                {
                                    'slug': 'healthpost',
                                    'name': 'Health Post',
                                    'children': []
                                    },
                                {
                                    'slug': 'dispensary',
                                    'name': 'Dispensary',
                                    'children': []
                                    },
                                ]
                            },
                        {
                            'slug': 'level_2',
                            'name': 'Level 2',
                            'children': [
                                {
                                    'slug': 'primaryhealthclinic',
                                    'name': 'Primary Health Clinic',
                                    'children': [],
                                    },
                                ]
                            },
                        {
                            'slug': 'level_3',
                            'name': 'Level 3',
                            'children': [
                                {
                                    'slug': 'primaryhealthcarecentre',
                                    'name': 'Primary Health Care Centre',
                                    'children': [],
                                    },
                                {
                                    'slug': 'comprehensivehealthcentre',
                                    'name': 'Comprehensive Health Centre',
                                    'children': [],
                                    },
                                {
                                    'slug': 'wardmodelprimaryhealthcarecentre',
                                    'name': 'Ward Model Primary Health Care Centre',
                                    'children': [],
                                    },
                                {
                                    'slug': 'maternity',
                                    'name': 'Maternity',
                                    'children': [],
                                    },
                                ],
                            },
                        {
                            'slug': 'level_4',
                            'name':  'Level 4',
                            'children': [
                                {
                                    'slug': 'cottagehospital',
                                    'name': 'Cottage Hospital',
                                    'children': [],
                                    },
                                {
                                    'slug': 'generalhospital',
                                    'name': 'General Hospital',
                                    'children': [],
                                    },
                                {
                                    'slug': 'specialisthospital',
                                    'name': 'Specialist Hospital',
                                    'children': [],
                                    },
                                {
                                    'slug': 'teachinghospital',
                                    'name': 'Teaching Hospital',
                                    'children': [],
                                    },
                                {
                                    'slug': 'federalmedicalcare',
                                    'name': 'Federal Medical Care',
                                    'children': [],
                                    },
                                ],
                            },
                        {
                            'slug': 'other',
                            'name': 'Other',
                            'children': [
                                {
                                    'slug': 'private',
                                    'name': 'Private',
                                    'children': [],
                                    },
                                {
                                    'slug': 'other',
                                    'name': 'Other',
                                    'children': [],
                                    },
                                ]
                            },
                        ],
                    },
                ],
            }

        def create_node(d, parent):
            children = d.pop('children')
            result = FacilityType.add_root(**d) if parent is None else parent.add_child(**d)
            for child in children:
                create_node(child, result)
            return result

        create_node(facility_types, None)

    @print_time
    def load_key_renames(self):
        kwargs = {
            'model': KeyRename,
            'path': os.path.join(self._data_dir, 'variables', 'key_renames.csv')
            }
        self.create_objects_from_csv(**kwargs)

    @print_time
    def create_objects_from_csv(self, model, path):
        csv_reader = CsvReader(path)
        for d in csv_reader.iter_dicts():
            model.objects.get_or_create(**d)

    @print_time
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

        csv_reader = CsvReader(os.path.join(self._data_dir, 'variables', 'variables.csv'))

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
                d['origin'] = Variable.get(slug=d['origin'])
                d['sector'] = Sector.objects.get(slug=d['sector'])
                lga_indicator, created = LGAIndicator.objects.get_or_create(**d)
            elif 'variable' in d and 'target' in d:
                d['variable'] = Variable.get(slug=d['variable'])
                d['target'] = Variable.get(slug=d['target'])
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
                    print "Variable import failed for data:", d

    @print_time
    def load_facilities(self):
        sectors = [
            {
                'sector': 'Education',
                'data_source': 'Educ_Baseline_PhaseII_all_merged_cleaned_07_20_2011.csv',
                },
            {
                'sector': 'Health',
                'data_source': 'Health_PhII_RoundI&II&III_Clean.csv',
                },
            {
                'sector': 'Water',
                'data_source': 'Water_PhaseII_RoundI&II&III_Clean.csv',
                },

            ]
        for sector in sectors:
            self.create_facilities_from_csv(**sector)

    @print_time
    def create_facilities_from_csv(self, sector, data_source):
        data_dir = os.path.join(self._data_dir, 'facility')
        path = os.path.join(data_dir, data_source)
        csv_reader = CsvReader(path)

        for d in csv_reader.iter_dicts():
            if '_lga_id' not in d:
                print "FACILITY MISSING LGA ID"
                continue
            if self._limit_import and d['_lga_id'] not in self.limit_lgas:
                continue
            d['_data_source'] = data_source
            d['_facility_type'] = sector.lower()
            d['sector'] = sector
            facility = FacilityBuilder.create_facility_from_dict(d)

    @print_time
    def load_lga_data(self):
        data_kwargs = [
            {
                'data': 'population',
                },
            {
                'data': 'area',
                },
            {
                'data': 'health',
                'row_contains_variable_slug': True,
                },
            {
                'data': 'education',
                'row_contains_variable_slug': True,
                },
            {
                'data': 'infrastructure',
                'row_contains_variable_slug': True,
                },
            {
                'data': 'LGA_Mang_Baseline_PhaseII_all_merged_cleaned_07_22_2011',
                },
            ]
        for kwargs in data_kwargs:
            filename = kwargs.pop('data') + '.csv'
            kwargs['path'] = os.path.join(self._data_dir, 'lga', filename)
            self.load_lga_data_from_csv(**kwargs)

    @print_time
    def load_lga_data_from_csv(self, path, row_contains_variable_slug=False):
        csv_reader = CsvReader(path)
        for d in csv_reader.iter_dicts():
            if '_lga_id' not in d:
                print "MISSING LGA ID:", d
                continue
            if self._limit_import and d['_lga_id'] not in self.limit_lgas:
                continue
            lga = LGA.objects.get(id=d['_lga_id'])
            if row_contains_variable_slug:
                if 'slug' in d and 'value' in d:
                    lga.add_data_from_dict({d['slug']: d['value']})
                else:
                    print "MISSING SLUG OR VALUE:", d
            else:
                lga.add_data_from_dict(d)

    @print_time
    def load_table_defs(self):
        """
        Table defs contain details to help display the data. (table columns, etc)
        """
        call_command('load_table_defs')

    @print_time
    def load_surveys(self):
        xfm_json_path = os.path.join('data','xform_manager_dataset.json')
        if not os.path.exists(xfm_json_path):
            raise Exception("Download and unpack xform_manager_dataset.json into project's data dir.")
        call_command('loaddata', xfm_json_path)

    @print_time
    def calculate_lga_indicators(self):
        for i in LGAIndicator.objects.all():
            i.set_lga_values()

    @print_time
    def calculate_lga_gaps(self):
        for i in GapVariable.objects.all():
            i.set_lga_values()

    def get_info(self):
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

        return {
            'number of facilities': Facility.objects.count(),
            'facilities without lgas': Facility.objects.filter(lga=None).count(),
            'number of facility records': FacilityRecord.objects.count(),
            'number of lga records': LGARecord.objects.count(),
            'unused variables': get_unused_variables(),
            }

    @print_time
    def print_stats(self):
        print json.dumps(self.get_info(), indent=4)

    def _drop_database(self):
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
