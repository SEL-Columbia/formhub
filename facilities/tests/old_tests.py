from django.test import TestCase
from facilities.facility_builder import FacilityBuilder
from facilities.models import CalculatedVariable, Variable, Facility, Sector, FacilityRecord, FacilityType, LGAIndicator
from nga_districts.models import Zone, State, LGA

class BasicDataTest(TestCase):
    def setUp(self):
        self.power = Variable.objects.create(
            slug='power', data_type='string'
            )
        self.has_water = Variable.objects.create(
            slug='has_water', data_type='boolean'
            )
        self.num_doctors = Variable.objects.create(
            slug='num_doctors', data_type='float'
            )

        self.zone = Zone.objects.create(name='Zone', slug='zone')
        self.state = State.objects.create(name='Zone', slug='zone', zone=self.zone)
        self.lga = LGA.objects.create(name='Local Govt Area', slug='lga', state=self.state)
        self.sector = Sector.objects.create(name='Test', slug='test')
        self.facility_type = FacilityType.add_root(name='Test', slug='test')
        self.facility = Facility.objects.create(facility_id='x', lga=self.lga, sector=self.sector, facility_type=self.facility_type)
        self.variable_values = [
                (self.power, 'none'),
                (self.has_water, True),
                (self.num_doctors, 10)
            ]
        for variable, value in self.variable_values:
            self.facility.set(variable, value)

    def test_get_all_data(self):
        latest_data = self.facility.get_latest_data()
        all_data = self.facility.get_all_data()
        expected_values = ['none', True, 10]
        varvals = [
                (self.power, 'none'),
                (self.has_water, True),
                (self.num_doctors, 10)
                ]
        for variable, value in varvals:
            variable_slug = variable.slug
            #check to see if get_latest_data has the right value
            self.assertEqual(latest_data[variable_slug], value)
            #chack to see if get_all_data gives the right value
            self.assertEqual(all_data[variable_slug].values()[0], value)

class CalculatedVariableTest(TestCase):

    def setUp(self):
        self.zone = Zone.objects.create(name='Zone', slug='zone')
        self.state = State.objects.create(name='State', slug='state', zone=self.zone)
        self.lga = LGA.objects.create(name='LGA', slug='LGA', state=self.state)
        self.sector = Sector.objects.create(name='Education', slug='education')
        self.facility_type = FacilityType.add_root(name='Education', slug='education')
        fields = ['slug', 'data_type', 'formula']
        data_dictionary_types = [
            ['student_teacher_ratio', 'float', "d['num_students_total'] / d['num_tchrs_total']"],
            ['sufficient_number_of_teachers', 'boolean', "d['student_teacher_ratio'] <= 35"],
            ['ideal_number_of_classrooms', 'float', "d['num_students_total'] / 35"],
            ]
        for ddt in data_dictionary_types:
            d = dict(zip(fields, ddt))
            CalculatedVariable.objects.get_or_create(**d)

    def test_calculated_variables_created(self):
        self.assertEquals(CalculatedVariable.objects.count(), 3)

    def test_student_teacher_ratio(self):
        """
        Test to make sure that when we create a school with number of
        students and number of teachers the student teacher ratio is
        automatically added to that school. Note: this only works if
        you use facility builder. Note how we create new calculated
        variables in the setUp method above.
        """
        d = {
            'sector': self.sector.name,
            '_lga_id': self.lga.id,
            '_facility_type': self.sector.slug,
            'num_students_total': 100,
            'num_tchrs_total': 20,
            }
        f = FacilityBuilder.create_facility_from_dict(d)
        self.assertEquals(
            f.get_latest_value_for_variable('student_teacher_ratio'),
            5
            )


class GapAnalysisTest(TestCase):

    def setUp(self):
        self.power = Variable.objects.create(
            slug='power', data_type='string'
            )
        self.has_water = Variable.objects.create(
            slug='has_water', data_type='boolean'
            )
        self.num_doctors = Variable.objects.create(
            slug='num_doctors', data_type='float'
            )

        self.zone = Zone.objects.create(name='Zone', slug='zone')
        self.state = State.objects.create(name='Zone', slug='zone', zone=self.zone)
        lga_names = ['LGA_1', 'LGA_2']
        self.lgas = [LGA.objects.create(name=n, slug=n, state=self.state) for n in lga_names]
        self.sector = Sector.objects.create(name='Test', slug='test')
        self.facility_type = FacilityType.add_root(name='Test', slug='test')
        self.facilities = []
        for lga in self.lgas:
            for facility_id in ['a', 'b', 'c', 'd']:
                self.facilities.append(
                    Facility.objects.create(facility_id=facility_id, lga=lga, sector=self.sector, facility_type=self.facility_type)
                    )
        for facility, value in zip(self.facilities, ['none', 'good', 'bad', 'none']):
            facility.set(self.power, value)
        for facility, value in zip(self.facilities, [True, False, True, False]):
            facility.set(self.has_water, value)
        for facility, value in zip(self.facilities, [10.0, 20.0, 10.0, 30.0]):
            facility.set(self.num_doctors, value)

    def tearDown(self):
        self.zone.delete()  # I think this should cascade
        self.power.delete()

    def test_count_by_variable(self):
        counts = FacilityRecord.counts_by_variable(self.lgas[0])
        expected_dict = {
            'test': {
                'power': {
                    'none': 2,
                    'good': 1,
                    'bad': 1,
                    },
                'has_water': {
                    True: 2,
                    False: 2,
                    },
                'num_doctors': {
                    10.0: 2,
                    20.0: 1,
                    30.0: 1,
                    },
                }
            }
        self.assertEquals(counts, expected_dict)

        counts = FacilityRecord.counts_of_boolean_variables(self.lgas[0])
        expected_dict = {'test': {'has_water': expected_dict['test']['has_water']}}
        self.assertEquals(counts, expected_dict)


class LGAIndicatorTest(TestCase):

    def setUp(self):
        self.has_water = Variable.objects.create(
            slug='has_water', data_type='boolean'
            )

        self.zone = Zone.objects.create(name='Zone', slug='zone')
        self.state = State.objects.create(name='Zone', slug='zone', zone=self.zone)
        lga_names = ['LGA_1', 'LGA_2']
        self.lgas = [LGA.objects.create(name=n, slug=n, state=self.state) for n in lga_names]
        self.sector = Sector.objects.create(name='Test', slug='test')
        self.facilities = []
        for lga in self.lgas:
            for facility_id in ['a', 'b']:
                self.facilities.append(
                    Facility.objects.create(facility_id=facility_id, lga=lga, sector=self.sector)
                    )
        self.assertEquals(len(self.facilities), 4)
        for facility, value in zip(self.facilities, [True, True, True, False]):
            facility.set(self.has_water, value)

        kwargs = {
            'name': 'Count of facilities with water',
            'slug': 'water_count',
            'data_type': 'float',
            'description': 'Count of facilities with water',
            'origin': self.has_water,
            'method': 'count_true',
            'sector': self.sector,
            }
        self.water_count = LGAIndicator.objects.create(**kwargs)

    def tearDown(self):
        self.zone.delete()  # I think this should cascade
        self.has_water.delete()
        self.sector.delete()

    def test_count_true(self):
        self.water_count.set_lga_values()
        self.assertEquals(
            self.lgas[0].get_latest_value_for_variable(self.water_count),
            2
            )
        self.assertEquals(
            self.lgas[1].get_latest_value_for_variable(self.water_count),
            1
            )

from django.test.client import Client
from django.contrib.auth.models import User
import json

class PassDataToPage(TestCase):
    def setUp(self):
        # I took this set up code from LGAIndicatorTest
        self.has_water = Variable.objects.create(
            slug='has_water', data_type='boolean'
            )
        self.zone = Zone.objects.create(name='Zone', slug='zone')
        self.state = State.objects.create(name='Zone', slug='zone', zone=self.zone)
        lga_names = ['LGA_1', 'LGA_2']
        self.lgas = [LGA.objects.create(name=n, slug=n, state=self.state, unique_slug='state_%s' % n) for n in lga_names]
        self.sector = Sector.objects.create(name='Test', slug='test')
        self.facilities = []
        ftype_root = FacilityType.add_root(slug='facility_type', name='Facility Type')
        ftype = ftype_root.add_child(name="Toilet", slug="toilet")
        for lga in self.lgas:
            for facility_id in ['a', 'b']:
                self.facilities.append(
                    Facility.objects.create(facility_id=facility_id, lga=lga, sector=self.sector, facility_type=ftype)
                    )
        self.assertEquals(len(self.facilities), 4)
        for facility, value in zip(self.facilities, [True, True, True, False]):
            facility.set(self.has_water, value)
        admin, created = User.objects.get_or_create(
                username="admin",
                email="admin@admin.com",
                is_staff=True,
                is_superuser=True
                )
        admin.set_password("pass")
        admin.save()
        self.client = Client()
        self.client.login(username='admin', password='pass')

    def test_lga_facility_json_url_works(self):
        # Right now, this test checks to see if the lga's facility json url is accessible
        self.assertTrue(LGA.objects.count() > 0)
        first_unique_slug = LGA.objects.all()[0].unique_slug
        response = self.client.get('/facilities/site/%s' % first_unique_slug)
        self.assertEqual(response.status_code, 200)

    def test_lga_facility_data(self):
        first_unique_slug = LGA.objects.all()[0].unique_slug
        response = self.client.get('/facilities/site/%s' % first_unique_slug)
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertTrue(isinstance(resp.get('facilities'), dict))
        self.assertTrue(isinstance(resp.get('profileData'), dict))


from facilities.score_variables import get_access_and_participation_score_variable, FunctionComponent, Function, components, build_score


class ScoreVariableTest(TestCase):

    def setUp(self):
        variable_slugs = [
            'net_intake_rate',
            'distance_from_catchment_area',
            'distance_to_nearest_secondary_school',
            'proportion_of_students_living_less_than_3km_away',
            'net_enrollment_ratio',
            'female_to_male_ratio',
            ]
        self.variables = {}
        for slug in variable_slugs:
            self.variables[slug] = Variable.objects.create(
                slug=slug, data_type='float'
                )

    def test_distance_component(self):
        # make sure the weight calculated from the distance for the
        # school is correct
        facility = Facility.objects.create()
        self.distance = self.variables['distance_from_catchment_area']
        facility.set(self.distance, 1.5) # 2 points
        access = get_access_and_participation_score_variable()

    def test_total_access_points(self):
        # test that the total score for all of the components is correct
        facility = Facility.objects.create()
        facility_data = [
            ('net_intake_rate', 0.97), # 5 points
            ('distance_from_catchment_area', 1.5), # 2 points
            ('distance_to_nearest_secondary_school', 0.5), # 2 points
            ('proportion_of_students_living_less_than_3km_away', 0.4), # 1 point
            ('net_enrollment_ratio', 0.75), # 2 points
            ('female_to_male_ratio', 0.9), # 2 points
            ] # total: 14 points
        for slug, value in facility_data:
            facility.set(self.variables[slug], value)
        access = get_access_and_participation_score_variable()
        self.maxDiff = None
        self.assertEquals(access.score_dict(facility), {
            'net_intake_rate': 5,
            'distance_from_catchment_area': 2,
            'distance_to_nearest_secondary_school': 2,
            'proportion_of_students_living_less_than_3km_away': 1,
            'net_enrollment_ratio': 2,
            'female_to_male_ratio': 2,
            })
        self.assertEquals(access.score(facility), 14.0)

    def test_field_storage(self):
        fc = FunctionComponent(1, 'x < 1', 'Does this work?')
        self.assertEquals(fc.to_dict(), {'value': 1, 'criteria': 'x < 1', 'label': 'Does this work?'})
        self.assertTrue(fc.meets_criteria(.3))

    def test_function(self):
        f = Function(
            [
                FunctionComponent(0, 'x < 0', 'Less than 0'),
                FunctionComponent(1, 'x >= 0', 'At least 0'),
                ]
            )
        self.assertEquals(f.points(5), 1)

    def test_build_score(self):
        s = build_score(components)
        self.assertEquals(
            s.score({
                    'net_intake_rate': 0.97,
                    'distance_from_catchment_area': 1.5,
                    'distance_to_nearest_secondary_school': 0.5,
                    'proportion_of_students_living_less_than_3km_away': 0.4,
                    'net_enrollment_ratio': 0.75,
                    'female_to_male_ratio': 0.9,
                    }),
            14.0
            )
