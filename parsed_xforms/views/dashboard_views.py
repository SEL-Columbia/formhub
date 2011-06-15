# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.db.models import Count
from django.template import RequestContext

import json

from parsed_xforms.models import ParsedInstance
from common_tags import *
from xform_manager.models import XForm, Instance
from nga_districts.models import LGA
from deny_if_unauthorized import deny_if_unauthorized
from collections import defaultdict
from xform_manager.models import SurveyType
from django.forms.models import model_to_dict
from django.conf import settings

@deny_if_unauthorized()
def dashboard(request):
    rc = RequestContext(request)
    rc.xforms = XForm.objects.all()
    rc.lga_table = submission_counts_by_lga(request, True)
    rc.table_types = json.dumps(dimensions.keys())
    rc.survey_types = [model_to_dict(s) for s in SurveyType.objects.all()]

    rc.zone_table = state_count_dict()
    
    rc.site_title = settings.SITE_TITLE
    
    rc.debug_mode = json.dumps(settings.DEBUG)
    
    return render_to_response(
        "dashboard.html",
        context_instance=rc
        )

@deny_if_unauthorized()
def submission_counts_by_lga(request, as_dict=False):
    titles = [u"Agriculture", u"Education", u"Health", u"LGA", u"Water"]
    headers = [u"Zone", u"State", u"LGA"] + titles

    dicts = ParsedInstance.objects.values("instance__xform__title", "lga").annotate(count=Count("id"))
    counts = defaultdict(dict)
    for d in dicts:
        counts[d['lga']][d['instance__xform__title']] = d['count']

    lgas = LGA.objects.order_by("state__zone__name", "state__name", "name").all()
    rows = []
    for lga in lgas:
        row = [lga.state.zone.name,
               lga.state.name,
               lga.name,]
        for title in titles:
            count = counts[lga.id].get(title, 0)
            row.append(count)
        rows.append(row)

    if as_dict:
        return {"headers": headers, "rows": rows}

    context = RequestContext(request, {"headers": headers, "rows": rows})
    return render_to_response(
        "submission_counts_by_lga.html",
        context_instance=context
        )

#used in dashboard() to get table_types //among other places?
dimensions = {
    "survey": "survey_type__slug",
    "surveyor": "surveyor__name",
    "date": "date",
    "location": "district",
    }
    
    
#state count dict is a beast
def state_count_dict():
    """
    This is similar to submission_counts_by_lga except the data is
    ordered by Zone, State, then LGA
    """
    lga_query = LGA.objects.order_by("state__zone__name", "state__name", "name")

    row_groups = []
    titles = [u"Agriculture", u"Education", u"Health", u"LGA", u"Water"]

    survey_totals = defaultdict(int)
    lgas_by_state = defaultdict(list)
    zone_totals = {}
    state_totals = {}
    lga_totals = {}
    total_total = 0

    states_list = []

    dicts = ParsedInstance.objects.values("instance__xform__title", "lga").annotate(count=Count("id"))
    counts = defaultdict(dict)
    for d in dicts:
        counts[d['lga']][d['instance__xform__title']] = d['count']

    for lga in lga_query.all():
        totals_for_this_lga = {}
        cur_state = lga.state
        cur_zone = cur_state.zone
        if cur_state not in states_list:
            states_list.append(cur_state)
        if cur_state not in state_totals:
            state_totals[cur_state] = defaultdict(int)
        if cur_zone not in zone_totals:
            zone_totals[cur_zone] = defaultdict(int)

        # this is one way to keep lga list so we can package it up
        # later.
        lgas_by_state[cur_state].append(lga)

        lga_total = 0
        for title in titles:
            count = counts[lga.id].get(title, 0)
            state_totals[cur_state][title] += count
            zone_totals[cur_zone][title] += count
            survey_totals[title] += count
            lga_total += count
            total_total += count
            totals_for_this_lga[title] = count

        totals_for_this_lga['total'] = lga_total
        lga_totals[lga] = totals_for_this_lga

    survey_totals_by_title = []
    for title in titles:
        survey_totals_by_title.append(survey_totals[title])

    for state in states_list:
        totals_by_title = []
        state_total = 0
        for title in titles:
            val = state_totals[state][title]
            totals_by_title.append(val)
            state_total += val
        lga_list = []
        for lga in lgas_by_state[state]:
            cur_lga_total = lga_totals[lga]
            lga_totals_by_title = []
            for title in titles:
                lga_totals_by_title.append(cur_lga_total[title])
            if cur_lga_total['total'] > 0:
                lga_list.append(
                    {
                        'name': lga.name,
                        'total_count': cur_lga_total['total'],
                        'pk': lga.id,
                        'survey_totals_by_title': lga_totals_by_title
                        }
                    )
        if state_total > 0:
            row_groups.append(
                {
                    'zone_name': state.zone.name,
                    'name': state.name,
                    'survey_totals_by_title': totals_by_title,
                    'total_count': state_total,
                    'lga_count': len(lga_list),
                    'lga_list': lga_list
                    }
                )

    return {
        'survey_titles': titles,
        'survey_totals_by_title': survey_totals_by_title,
        'states': row_groups,
        'total_total': total_total
    }