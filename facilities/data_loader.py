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
import codecs

from django.core.mail import mail_admins
import sys

class DataLoader(object):

    def __init__(self, **kwargs):
        self._debug = kwargs.get('debug', False)
        self._data_dir = kwargs.get('data_dir', 'data')
        self._load_config_file()

    def _load_config_file(self):
        path = os.path.join(self._data_dir, 'data_configurations.json')
        with open(path) as f:
            self._config = json.load(f)

    def setup(self):
        self.reset_database()
        self.load_system()

    def load(self, lga_ids=[]):
        self.lga_ids = lga_ids

        lgas = []
        for lga_id in lga_ids:
            try:
                lgas.append(LGA.objects.get(id=lga_id))
            except LGA.DoesNotExist:
                continue
        for lga in lgas:
            lga.data_load_in_progress = True
            lga.save()
        for lga in lgas:
            self.lga_ids = [str(lga.id)]
            try:
                self.load_data()
                self.load_calculations()
                lga.data_load_in_progress = False
                lga.data_loaded = True
                lga.save()
            except KeyboardInterrupt:
                sys.exit(0)
            except Exception, e:
                lga.data_load_in_progress = False
                lga.data_loaded = False
                lga.save()
                mail_admins("Problems with loading data from lga id: %s" % str(lga.id),
                """I wasn't gonna say anything but [LGA ID:%s] is seriously causing problems with the load script. You guys might want to check it out.

Sincerely,
NMIS

PS. some exception data: %s""" % (str(lga.id), str(e)))
        self.lga_ids = lga_ids

    @print_time
    def reset_database(self):
        self._drop_database()
        call_command('syncdb', interactive=False)

    def load_system(self):
        self.create_users()
        self.create_sectors()
        self.create_facility_types()
        self.load_lga_districts()
        self.load_key_renames()
        self.load_variables()
        self.load_table_defs()
        self.mark_available_lgas()

    @print_time
    def mark_available_lgas(self):
        lga_ids = []
        facility_csv_files = [ff['data_source'] for ff in self._config['facility_csvs']]
        #this process takes about 6 seconds...
        for csv_file in facility_csv_files:
            data_dir = os.path.join(self._data_dir, 'facility_csvs')
            path = os.path.join(data_dir, csv_file)
            csv_reader = CsvReader(path)
            for d in csv_reader.iter_dicts():
                lga_id = d.get('_lga_id')
                if lga_id is not None and lga_id not in lga_ids:
                    lga_ids.append(lga_id)
        for lga_id in lga_ids:
            try:
                lga = LGA.objects.get(id=lga_id)
                lga.data_available=True
                lga.save()
            except LGA.DoesNotExist, e:
                print "lga not found: %s" % str(lga_id)
        print "%d LGAs have data" % LGA.objects.filter(data_available=True).count()

    def load_data(self, lga_ids=[]):
        self.load_facilities()
        self.load_lga_data()

    def load_calculations(self):
        self.calculate_lga_indicators()
        self.calculate_lga_gaps()
        self.calculate_lga_variables()

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

        from django.contrib.sites.models import Site
        if Site.objects.count() == 1:
            site = Site.objects.all()[0]
            site.domain = settings.MAIN_SITE_HOSTNAME
            site.name = settings.MAIN_SITE_HOSTNAME
            site.save()

    @print_time
    def create_sectors(self):
        sectors = ['Education', 'Health', 'Water']
        for sector in sectors:
            Sector.objects.get_or_create(slug=sector.lower(), name=sector)

    @print_time
    def create_facility_types(self):
        def create_node(d, parent):
            children = d.pop('children')
            result = FacilityType.add_root(**d) if parent is None else parent.add_child(**d)
            for child in children:
                create_node(child, result)
            return result

        with codecs.open('facilities/fixtures/facility_types.json', 'r', encoding='utf-8') as f:
            facility_types = json.load(f)
            create_node(facility_types, None)

    @print_time
    def load_key_renames(self):
        kwargs = {
            'model': KeyRename,
            'path': os.path.join(self._data_dir, 'variables', 'key_renames.csv')
            }
        self.create_objects_from_csv(**kwargs)

    @print_time
    def load_lga_districts(self):
        districts_json_path = os.path.join(self._data_dir, 'districts', 'districts.json')
        if os.path.exists(districts_json_path):
            call_command("loaddata", districts_json_path)

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

        def cls_variable_loader(cls):
            def create_instance_of_cls_with_d(d):
                if self._debug:
                    cls.objects.get_or_create(**d)
                else:
                    try:
                        cls.objects.get_or_create(**d)
                    except:
                        print "%s import failed for data: %s" % (cls.__name__, str(d))
            return create_instance_of_cls_with_d

        def dict_is_valid_var(d):
            if 'data_type' not in d:
                return False
            elif 'COMMENTS' in d:
                return False
            return True

        def load_variable_file_with_loader(variable_file, loader):
            file_path = os.path.join(self._data_dir, 'variables', variable_file)
            for d in CsvReader(file_path).iter_dicts():
                if dict_is_valid_var(d):
                    loader(d)

        def load_lga_variable(d):
            d['origin'] = Variable.get(slug=d['origin'])
            d['sector'] = Sector.objects.get(slug=d['sector'])
            cls_variable_loader(LGAIndicator)(d)

        def gap_loader(d):
            d['variable'] = Variable.get(slug=d['variable'])
            d['target'] = Variable.get(slug=d['target'])
            cls_variable_loader(GapVariable)(d)

        variable_loader_methods = {
            'partition': cls_variable_loader(PartitionVariable),
            'calculated': cls_variable_loader(CalculatedVariable),
            'lga': load_lga_variable,
            'gap': gap_loader,
            'default': cls_variable_loader(Variable)
        }
        for variable_file_data in self._config['variables']:
            load_method = variable_loader_methods.get(variable_file_data.get('type', 'default'))
            load_variable_file_with_loader(variable_file_data.get('data_source'), load_method)

    @print_time
    def load_facilities(self):
        for facility_csv in self._config['facility_csvs']:
            self.create_facilities_from_csv(**facility_csv)

    @print_time
    def create_facilities_from_csv(self, sector, data_source):
        path = os.path.join(self._data_dir, 'facility_csvs', data_source)
        for d in CsvReader(path).iter_dicts():
            if '_lga_id' not in d:
                print "FACILITY MISSING LGA ID"
                continue
            if d['_lga_id'] not in self.lga_ids:
                continue
            d['_data_source'] = data_source
            d['_facility_type'] = sector.lower()
            d['sector'] = sector
            facility = FacilityBuilder.create_facility_from_dict(d)

    @print_time
    def load_lga_data(self):
        data_kwargs = self._config['lga']
        for kwargs_original in data_kwargs:
            kwargs = kwargs_original.copy()
            data_source = kwargs.pop('data_source')
            kwargs['path'] = os.path.join(self._data_dir, 'lga', data_source)
            self.load_lga_data_from_csv(**kwargs)

    @print_time
    def load_lga_data_from_csv(self, path, row_contains_variable_slug=False):
        csv_reader = CsvReader(path)
        for d in csv_reader.iter_dicts():
            if '_lga_id' not in d:
                print "MISSING LGA ID:", d
                continue
            if d['_lga_id'] not in self.lga_ids:
                continue
            lga = LGA.objects.get(id=d['_lga_id'])
            if row_contains_variable_slug:
                if 'slug' in d and 'value' in d:
                    lga.add_data_from_dict({d['slug']: d['value']})
                else:
                    print "MISSING SLUG OR VALUE:", d
            else:
                lga.add_data_from_dict(d, and_calculate=True)

    @print_time
    def load_table_defs(self):
        """
        Table defs contain details to help display the data. (table columns, etc)
        """
        from facility_views.models import FacilityTable, TableColumn, ColumnCategory, MapLayerDescription
        def delete_existing_table_defs():
            FacilityTable.objects.all().delete()
            TableColumn.objects.all().delete()
            ColumnCategory.objects.all().delete()
            MapLayerDescription.objects.all().delete()
        delete_existing_table_defs()
        subgroups = {}
        def load_subgroups():
            sgs = list(CsvReader(os.path.join(self._data_dir,"table_definitions", "subgroups.csv")).iter_dicts())
            for sg in sgs:
                if 'slug' in sg:
                    subgroups[sg['slug']] = sg['name']
            return subgroups
        load_subgroups()
        def load_table_types(table_types):
            for tt_data in table_types:
                name = tt_data['name']
                slug = tt_data['slug']
                data_source = tt_data['data_source']
                curtable = FacilityTable.objects.create(name=name, slug=slug)
                csv_reader = CsvReader(os.path.join(self._data_dir,"table_definitions", data_source))
                display_order = 0
                for input_d in csv_reader.iter_dicts():
                    subs = []
                    if 'subgroups' in input_d:
                        for sg in input_d['subgroups'].split(" "):
                            if sg in subgroups:
                                subs.append({'name': subgroups[sg], 'slug': sg})
                    for sub in subs:
                        curtable.add_column(sub)
                    try:
                        input_d['display_order'] = display_order
                        d = TableColumn.load_row_from_csv(input_d)
                        display_order += 1
                        curtable.add_variable(d)
                    except:
                        print "Error importing table definition for data: %s" % input_d
        load_table_types(self._config['table_definitions'])
        def load_layer_descriptions(ld):
            for layer_file in ld:
                file_name = os.path.join(self._data_dir,"map_layers", layer_file['data_source'])
                layer_descriptions = list(CsvReader(file_name).iter_dicts())
                if layer_file['type'] == "layers":
                    for layer in layer_descriptions:
                        MapLayerDescription.objects.get_or_create(**layer)
                elif layer_file['type'] == "legend_data":
                    layers = defaultdict(list)
                    for layer in layer_descriptions:
                        lslug = layer['slug']
                        lstr = ','.join([layer['value'],\
                                        layer['opacity'],\
                                        layer['color']])
                        layers[lslug].append(lstr)
                    for layer_slug, legend_values in layers.items():
                        try:
                            ml = MapLayerDescription.objects.get(slug=layer_slug)
                            ml.legend_data = ';'.join(legend_values)
                            ml.save()
                        except MapLayerDescription.DoesNotExist:
                            continue
        load_layer_descriptions(self._config['map_layers'])

    @print_time
    def load_surveys(self):
        xfm_json_path = os.path.join('data','xform_manager_dataset.json')
        if not os.path.exists(xfm_json_path):
            raise Exception("Download and unpack xform_manager_dataset.json into project's data dir.")
        call_command('loaddata', xfm_json_path)

    @print_time
    def calculate_lga_indicators(self):
        for i in LGAIndicator.objects.all():
            i.set_lga_values(self.lga_ids)

    @print_time
    def calculate_lga_gaps(self):
        for i in GapVariable.objects.all():
            i.set_lga_values(self.lga_ids)

    @print_time
    def calculate_lga_variables(self):
        lgas = LGA.objects.filter(id__in=[int(x) for x in self.lga_ids])
        for lga in lgas:
            lga.add_calculated_values(lga.get_latest_data(), only_for_missing=True)

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

def _lga_list_is_all(ll):
    return ll == "all" or isinstance(ll, list) and ll[0] == "all"

def load_lgas(lga_ids, individually=True):
    """
    Currently, this function is only called by the management command "load_lgas"
    which is in charge of starting a subprocess.
    """
    if _lga_list_is_all(lga_ids):
        lgas_with_data = LGA.objects.filter(data_available=True).values('id')
        lga_ids = [l['id'] for l in lgas_with_data]
    data_loader = DataLoader()
    for lga_id in lga_ids:
        data_loader.load([lga_id])
        print "Finished loading LGA: %s" % (str(lga_id))
    data_loader.print_stats()
