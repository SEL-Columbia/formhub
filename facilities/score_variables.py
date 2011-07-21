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
        print point_test_dict
        for points, test in point_test_dict.iteritems():
            value = facility.get(component_slug)
            if self._passes_test(test, value):
                if result is not None:
                    # ensure there are no overlapping criteria
                    raise Exception("Unsure how many points should be assigned in this score variable.")
                result = float(points)
        return 0 if result is None else result

# create some score variables in this file that we'll want to test.
def get_access_and_participation_score_variable():
    components = {
        'distance': {
            3: 'x < 1',
            2: '1 <= x and x < 2',
            1: '2 <= x',
            }
        }
    result = ScoreVariable()
    result.set_components(components)
    return result
