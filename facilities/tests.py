from django.test import TestCase
from facility_builder import FacilityBuilder
from models import CalculatedVariable


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
