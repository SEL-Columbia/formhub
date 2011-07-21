from django.db import models
from abstract_models import Variable
import json


class ScoreVariable(Variable):

    components = models.TextField()

    def set_components(self, pyobj):
        self.components = json.dumps(pyobj)

    def get_components(self):
        return json.loads(self.components)

    _components = property(get_components, set_components)

    def _passes_test(self, test_str, value):
        f = lambda x: eval(test_str)
        return f(value)

    def _get_component_dict(self):
        return dict([(c.pop('slug'), c) for c in self._components])

    def _get_function(self, slug):
        return self._get_component_dict()[slug]['function']

    def points(self, facility, slug):
        """
        Return the number of points this facility earns for this
        particular component.
        """
        value = facility.get(slug)
        result = None
        for function_component in self._get_function(slug):
            if self._passes_test(function_component['criteria'], value):
                if result is not None:
                    # ensure there are no overlapping criteria
                    raise Exception("Unsure how many points should be assigned in this score variable.")
                result = function_component['value']
        return 0 if result is None else result

    def score_dict(self, facility):
        return dict([(c['slug'], self.points(facility, c['slug'])) for c in self._components])

    def score(self, facility):
        """
        Return the total score for this facility (sum of all the components).
        """
        return sum(self.score_dict(facility).values())

    def get_display_info(self, facility):
        """
        Return something like:
        {
        'net_intake_rate': {'value': 0.5, 'group_label': "Below 80%', 'points': 2},
        ...
        }
        """
        pass


# create some score variables in this file that we'll want to test.
def get_access_and_participation_score_variable():
    components = [
        # net intake rate should only be used at the primary and js levels,
        # right now we're going to ignore that.
        {
            'slug': 'net_intake_rate',
            'label': 'Net intake rate',
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
    result = ScoreVariable()
    result.set_components(components)
    return result
