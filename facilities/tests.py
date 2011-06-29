from django.test import TestCase
from facility_builder import FacilityBuilder
from models import CalculatedVariable, Variable, Facility, FacilityRecord
from nga_districts.models import Zone, State, LGA

class CalculatedVariableTest(TestCase):

    def setUp(self):
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
            '_facility_type': 'School',
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

        self.zone = Zone.objects.create(name='Zone', slug='zone')
        self.state = State.objects.create(name='Zone', slug='zone', zone=self.zone)
        lga_names = ['LGA_1', 'LGA_2']
        self.lgas = [LGA.objects.create(name=n, slug=n, state=self.state) for n in lga_names]
        self.facilities = []
        for lga in self.lgas:
            for facility_id in ['a', 'b']:
                self.facilities.append(
                    Facility.objects.create(facility_id=facility_id, lga=lga)
                    )
        for facility, value in zip(self.facilities, ['none', 'good', 'none', 'none']):
            facility.set(self.power, value)

    def tearDown(self):
        self.zone.delete()  # I think this should cascade
        self.power.delete()

    def test_count_by_lga(self):
        counts = FacilityRecord.count_by_lga(self.power)
        expected_dict = {
            1: {
                'none': 1,
                'good': 1,
                },
            2: {
                'none': 2,
                },
            }
        self.assertEquals(counts, expected_dict)









