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

    def points(self, facility, component_slug):
        """
        Return the number of points this facility earns for this
        particular component.
        """
        result = None
        point_test_dict = self._components[component_slug]
        for points, test in point_test_dict.iteritems():
            value = facility.get(component_slug)
            if self._passes_test(test, value):
                if result is not None:
                    # ensure there are no overlapping criteria
                    raise Exception("Unsure how many points should be assigned in this score variable.")
                result = float(points)
        return 0 if result is None else result

    def score_dict(self, facility):
        return dict([(slug, self.points(facility, slug)) for slug in self._components])

    def score(self, facility):
        """
        Return the total score for this facility (sum of all the components).
        """
        return sum(self.score_dict(facility).values())


# create some score variables in this file that we'll want to test.
def get_access_and_participation_score_variable():
    components = {
        # net intake rate should only be used at the primary and js levels,
        # right now we're going to ignore that.
        'net_intake_rate': {
            5: 'x > 0.95',
            3: '0.80 <= x and x <= 0.95',
            2: 'x < 0.80',
            },
        'distance_from_catchment_area': {
            3: 'x < 1',
            2: '1 <= x and x < 2',
            1: '2 <= x',
            },
        'distance_to_nearest_secondary_school': {
            2: 'x < 1',
            1: '1 <= x and x < 2',
            0: '2 <= x',
            },
        'proportion_of_students_living_less_than_3km_away': {
            3: 'x > 0.90',
            2: '0.50 <= x and x <= 0.90',
            1: 'x < 0.50',
            },
        'net_enrollment_ratio': {
            5: 'x > 0.95',
            2: '0.50 <= x and x <= 0.95',
            1: 'x < 0.50',
            },
        'female_to_male_ratio': {
            4: 'x > 0.90',
            2: '0.50 <= x and x <= 0.90',
            1: 'x < 0.50',
            },
        }
    result = ScoreVariable()
    result.set_components(components)
    return result
