# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from pyxform.question import SelectOneQuestion, Question
from pyxform.xls2json import print_pyobj_to_json
from pyxform.survey import Survey
from nga_districts.models import Zone, State, LGA


class LocationQuestions(object):
    """
    This stuff would clearly be improved by using a tree library.
    """

    def set_lgas(self, query_set):
        self._lgas = query_set
        self._lgas = self._lgas.distinct().order_by("name")
        self._states = State.objects.filter(lgas__in=self._lgas)
        self._states = self._states.distinct().order_by("name")
        self._zones = Zone.objects.filter(states__in=self._states)
        self._zones = self._zones.distinct().order_by("name")
        for i in self._zones:
            print i.name

    def select_zone(self):
        result = SelectOneQuestion(label=u"Zone", name=u"zone")
        for zone in self._zones:
            result.add_choice(label=zone.name, name=zone.slug)
        return result

    def select_state(self, zone):
        result = SelectOneQuestion(label=u"State",
                                   name=u"state_in_%s" % zone.slug)
        result.set(Question.BIND, {u"relevant": u"${zone}='%s'" % zone.slug})
        qs = self._states.filter(zone=zone)
        for state in qs:
            result.add_choice(label=state.name, name=state.slug)
        return result

    def select_state_questions(self):
        return [self.select_state(zone) for zone in self._zones]

    def select_lga(self, state):
        result = SelectOneQuestion(label=u"LGA",
                                   name=u"lga_in_%s" % state.slug)
        binding = {
            u"relevant": u"${state_in_%(zone)s}='%(state)s'" % {
                u"zone": state.zone.slug,
                u"state": state.slug
                }
            }
        result.set(Question.BIND, binding)
        qs = self._lgas.filter(state=state)
        for lga in qs:
            result.add_choice(label=lga.name, name=lga.slug)
        return result

    def select_lga_questions(self):
        return [self.select_lga(state) for state in self._states]

    def select_zone_state_lga(self):
        survey = Survey(name=u"need_xml_tag")
        survey.set(u"type", u"survey")
        questions = [self.select_zone()] + \
            self.select_state_questions() + \
            self.select_lga_questions()
        for question in questions:
            survey.add_child(question)
        pyobj = survey.to_dict()
        print_pyobj_to_json(pyobj, "zone_state_lga.json")


location_questions = LocationQuestions()
lgas_in_malaria_survey = LGA.objects.filter(included_in_malaria_survey=True)
location_questions.set_lgas(lgas_in_malaria_survey)
location_questions.select_zone_state_lga()
