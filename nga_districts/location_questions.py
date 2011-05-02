#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from django.core.management.base import BaseCommand
from pyxform.question import SelectOneQuestion, Question
from pyxform.xls2json import print_pyobj_to_json
from pyxform.survey import Survey
from models import Zone, State, LGA

def select_zone():
    result = SelectOneQuestion(label=u"Zone", name=u"zone")
    qs = Zone.get_query_set_for_round(3).order_by("name")
    for zone in qs:
        result.add_choice(label=zone.name, name=zone.slug)
    return result

def select_state(zone):
    result = SelectOneQuestion(label=u"State", name=u"state_in_%s" % zone.slug)
    result.set(Question.BIND, {u"relevant" : u"${zone}='%s'" % zone.slug})
    qs = State.get_query_set_for_round(3).filter(zone=zone).order_by("name")
    for state in qs:
        result.add_choice(label=state.name, name=state.slug)
    return result

def select_state_questions():
    return [select_state(zone) for zone in Zone.get_query_set_for_round(3)]

def select_lga(state):
    result = SelectOneQuestion(label=u"LGA", name=u"lga_in_%s" % state.slug)
    result.set(Question.BIND, {u"relevant" : u"${state_in_%(zone)s}='%(state)s'" % {u"zone" : state.zone.slug, u"state" : state.slug}})
    qs = LGA.get_query_set_for_round(3).filter(state=state).order_by("name")
    for lga in qs:
        result.add_choice(label=lga.name, name=lga.slug)
    return result

def select_lga_questions():
    return [select_lga(state) for state in State.get_query_set_for_round(3)]

def select_zone_state_lga():
    survey = Survey(name=u"need_xml_tag")
    survey.set(u"type", u"survey")
    questions = [select_zone()] + \
        select_state_questions() + \
        select_lga_questions()
    for question in questions:
        survey.add_child(question)
    pyobj = survey.to_dict()
    print_pyobj_to_json(pyobj, "zone_state_lga.json")
