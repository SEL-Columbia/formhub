from django.db import models
from abstract_models import Variable
import json


class ScoreVariable(Variable):

    score_json = models.TextField()

    def set_score(self, pyobj):
        """
        TODO: Clean this up a bit.
        """
        self.score_json = json.dumps(pyobj)

    def get_score(self):
        return build_score(json.loads(self.score_json))

    _score = property(get_score, set_score)

    def score_dict(self, facility):
        return self._score.score_dict(facility.get_latest_data())

    def score(self, facility):
        return sum(self.score_dict(facility).values())

    def maximum_score(self, facility):
        return self._score.maximum(facility.get_latest_data())

    def get_display_info(self, facility):
        """
        Return something like:
        {
        'net_intake_rate': {'value': 0.5, 'group_label': "Below 80%', 'points': 2},
        ...
        }
        """
        pass


class FieldStorage(object):

    def __init__(self, *args, **kwargs):
        if len(args) > 0:
            assert len(kwargs.keys()) == 0
            kwargs = dict(zip(self.FIELDS, args))
        assert sorted(kwargs.keys()) == sorted(self.FIELDS), "kwargs: %s, FIELDS: %s" % (kwargs, self.FIELDS)
        for k, v in kwargs.items():
            setattr(self, k, v)

    def to_dict(self):
        return dict([(k, getattr(self, k)) for k in self.FIELDS])


class Score(FieldStorage):

    FIELDS = ['component_list']

    def score_dict(self, d):
        """
        d is a dictionary of data, like {net_intake_rate: 3, ...}
        """
        return dict([(c.slug, c.function.points(d[c.slug])) for c in self.component_list if c.applies_to(d)])

    def score(self, d):
        """
        Return the total score for this facility (sum of all the components).
        """
        return sum(self.score_dict(d).values())

    def maximum(self, d):
        return sum([c.function.maximum_value() for c in self.component_list if c.applies_to(d)])


class ScoreComponent(FieldStorage):

    FIELDS = ['slug', 'label', 'function', 'limit_by', 'limit_to']

    def applies_to(self, d):
        """
        check whether or not to score this component based on limit_by (field to check)
        and limit_to (list of valid values)
        """
        if self.limit_by is None or self.limit_to is None:
            return True
        elif self.limit_by in d and d[self.limit_by] in self.limit_to:
            return True
        else:
            return False


class Function(FieldStorage):

    FIELDS = ['component_list']

    def points(self, value):
        result = None
        for function_component in self.component_list:
            if function_component.meets_criteria(value):
                if result is not None:
                    # ensure there are no overlapping criteria
                    raise Exception("Unsure how many points should be assigned in this score variable.")
                result = function_component.value
        assert result is not None, "This value does not satisfy any criteria."
        return result

    def maximum_value(self):
        return max([c.value for c in self.component_list])


class FunctionComponent(FieldStorage):

    FIELDS = ['value', 'criteria', 'label']

    def meets_criteria(self, value):
        f = lambda x: eval(self.criteria)
        return f(value)


def build_score(s):
    return Score(
        [
            ScoreComponent(
                sc['slug'],
                sc['label'],
                Function(
                    [FunctionComponent(**fc) for fc in sc['function']]
                    ),
                sc['limit_by'],
                sc['limit_to']
                )
            for sc in s
            ]
        )


# create some score variables in this file that we'll want to test.

health_min_lab_diagnostics_components = [
    {
        'slug': 'lab_tests_malaria_rdt',
        'label': 'RDT (Malaria)',
        'limit_by': None,
        'limit_to': None,
        'function': [
            {
                'value': 1,
                'criteria': 'x',
                'label': 'Yes',
                },
            {
                'value': 0,
                'criteria': 'not x',
                'label': 'No',
                },
            ],
        },
    {
        'slug': 'lab_tests_hemoglobin_testing',
        'label': 'Hemoglobin',
        'limit_by': None,
        'limit_to': None,
        'function': [
            {
                'value': 1,
                'criteria': 'x',
                'label': 'Yes',
                },
            {
                'value': 0,
                'criteria': 'not x',
                'label': 'No',
                },
            ],
        },
    {
        'slug': 'lab_tests_stool',
        'label': 'Stool',
        'limit_by': 'facility_type',
        'limit_to': ['primaryhealthcarecentre', 'comprehensivehealthcentre', 'wardmodelprimaryhealthcarecentre', 'maternity', 'cottagehospital', 'generalhospital', 'specialisthospital', 'teachinghospital', 'federalmedicalcare'],
        'function': [
            {
                'value': 1,
                'criteria': 'x',
                'label': 'Yes',
                },
            {
                'value': 0,
                'criteria': 'not x',
                'label': 'No',
                },
            ],
        },
    {
        'slug': 'lab_tests_urine_testing',
        'label': 'Urine',
        'limit_by': None,
        'limit_to': None,
        'function': [
            {
                'value': 1,
                'criteria': 'x',
                'label': 'Yes',
                },
            {
                'value': 0,
                'criteria': 'not x',
                'label': 'No',
                },
            ],
        },
    {
        'slug': 'lab_tests_pregnancy',
        'label': 'Pregnancy',
        'limit_by': None,
        'limit_to': None,
        'function': [
            {
                'value': 1,
                'criteria': 'x',
                'label': 'Yes',
                },
            {
                'value': 0,
                'criteria': 'not x',
                'label': 'No',
                },
            ],
        },
    ]

education_access_and_participation_components = [
    # net intake rate should only be used at the primary and js levels,
    # right now we're going to ignore that.
    {
        'slug': 'net_intake_rate',
        'label': 'Net intake rate',
        'limit_by': None,
        'limit_to': None,
        'function': [
            {
                'value': 5,
                'criteria': 'x > 0.95',
                'label': 'Above 95%',
                },
            {
                'value': 3,
                'criteria': '0.80 <= x and x <= 0.95',
                'label': 'Between 80% and 95%',
                },
            {
                'value': 2,
                'criteria': 'x < 0.80',
                'label': 'Less than 80%',
                },
            ]
        },
    {
        'slug': 'distance_from_catchment_area',
        'label': 'Distance from catchment area',
        'limit_by': None,
        'limit_to': None,
        'function': [
            {
                'value': 3,
                'criteria': 'x < 1',
                'label': 'Less than 1km',
                },
            {
                'value': 2,
                'criteria': '1 <= x and x < 2',
                'label': 'Between 1km and 2km',
                },
            {
                'value': 1,
                'criteria': '2 <= x',
                'label': 'More than 2km',
                },
            ]
        },
    {
        'slug': 'distance_to_nearest_secondary_school',
        'label': 'Distance to nearest secondary school',
        'limit_by': None,
        'limit_to': None,
        'function': [
            {
                'value': 2,
                'criteria': 'x < 1',
                'label': 'Less than 1km',
                },
            {
                'value': 1,
                'criteria': '1 <= x and x < 2',
                'label': 'Between 1km and 2km',
                },
            {
                'value': 0,
                'criteria': '2 <= x',
                'label': 'More than 2km',
                },
            ]
        },
    {
        'slug': 'proportion_of_students_living_less_than_3km_away',
        'label': 'Proportion of students living less than 3km away',
        'limit_by': None,
        'limit_to': None,
        'function': [
            {
                'value': 3,
                'criteria': 'x > 0.90',
                'label': 'More than 90%',
                },
            {
                'value': 2,
                'criteria': '0.50 <= x and x <= 0.90',
                'label': 'Between 50% and 90%',
                },
            {
                'value': 1,
                'criteria': 'x < 0.50',
                'label': 'Less than 50%',
                },
            ]
        },
    {
        'slug': 'net_enrollment_ratio',
        'label': 'Net enrollment ratio',
        'limit_by': None,
        'limit_to': None,
        'function': [
            {
                'value': 5,
                'criteria': 'x > 0.95',
                'label': 'More than 95%',
                },
            {
                'value': 2,
                'criteria': '0.50 <= x and x <= 0.95',
                'label': 'Between 50% and 95%',
                },
            {
                'value': 1,
                'criteria': 'x < 0.50',
                'label': 'Less than 50%',
                },
            ]
        },
    {
        'slug': 'female_to_male_ratio',
        'label': 'Female to male ratio',
        'limit_by': None,
        'limit_to': None,
        'function': [
            {
                'value': 4,
                'criteria': 'x > 0.90',
                'label': 'More than 90%',
                },
            {
                'value': 2,
                'criteria': '0.50 <= x and x <= 0.90',
                'label': 'Between 50% and 90%',
                },
            {
                'value': 1,
                'criteria': 'x < 0.50',
                'label': 'Less than 50%',
                },
            ]
        },
    ]

def get_education_access_and_participation_score_variable():
    result = ScoreVariable(slug='education_access_and_participation_score')
    result.set_score(education_access_and_participation_components)
    return result

def get_health_min_lab_diagnostics_score_variable():
    result = ScoreVariable(slug='health_min_lab_diagnostics_score')
    result.set_score(health_min_lab_diagnostics_components)
    return result
