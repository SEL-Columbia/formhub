#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from django.core.management.base import BaseCommand
from pyxform.question import SelectOneQuestion, Question
from pyxform.xls2json import print_pyobj_to_json
from models import Zone, State, LGA

def select_zone():
    result = SelectOneQuestion(label=u"Zone", name=u"zone")
    qs = Zone.get_phase2_query_set().order_by("name")
    for zone in qs:
        result.add_choice(label=zone.name, value=zone.slug)
    return result

def select_state(zone):
    result = SelectOneQuestion(label=u"State", name=u"state_in_%s" % zone.slug)
    result.set(Question.BIND, {u"relevant" : u"zone='%s'" % zone.slug})
    qs = State.get_phase2_query_set().filter(zone=zone).order_by("name")
    for state in qs:
        result.add_choice(label=state.name, value=state.slug)
    return result

def select_state_questions():
    return [select_state(zone) for zone in Zone.get_phase2_query_set()]

def select_lga(state):
    result = SelectOneQuestion(label=u"LGA", name=u"lga_in_%s" % state.slug)
    result.set(Question.BIND, {u"relevant" : u"state_in_%(zone)s='%(state)s'" % {u"zone" : state.zone.slug, u"state" : state.slug}})
    qs = LGA.get_phase2_query_set().filter(state=state).order_by("name")
    for lga in qs:
        result.add_choice(label=lga.name, value=lga.slug)
    return result

def select_lga_questions():
    return [select_lga(state) for state in State.get_phase2_query_set()]

def select_zone_state_lga():
    questions = [select_zone()] + \
        select_state_questions() + \
        select_lga_questions()
    pyobj = [q.to_dict() for q in questions]
    print_pyobj_to_json(pyobj, "zone_state_lga.json")
