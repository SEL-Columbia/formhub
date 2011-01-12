#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
    Various helpers and shortcuts
"""

import string
import datetime
from StringIO import StringIO

from xlwt import *
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _

from rapidsms.contrib.handlers.exceptions import ExitHandle

from simple_locations.models import Area

from report_parts.models import Report
from models import Results


def check_location(location_code, location_type=None):
    """
        Exit the handle if the location does not exists.
        
        If it does, returns it.
    """
    
    try:
        location = Area.objects.get(code__iexact=location_code)
    except Area.DoesNotExist:
    
        raise ExitHandle(_(u"The code %(code)s doesn't match any known "\
                           u"location. Ask your administrator the right code "\
                           u"for your location") % {'code': location_code})
    else:
        if location_type and location.type.slug != slugify(location_type):
            current_type = location.type.name
            expected_type = AreaType.objects.get(slug=slugify(location_type)).name
            raise ExitHandle(_(u"You can only do this with a %(expected_type)s"\
                               u" but %(location)s is a %(current_type)s.") % {
                               'expected_type': _(expected_type),
                               'location': location,
                               'current_type': _(current_type)})
                               
    return location                        


    
def fix_date_year(date):
    """
        If the date if not provided with the year, get the closest year.
        Makes sure the date is in the past.
    """
    
    if date.year == 1900:
        now = datetime.datetime.today()
        date = datetime.datetime(now.year, date.month, date.day)
        
        if date > now:
            date = datetime.datetime(now.year - 1, date.month, date.day)
        
    return date           
    
    
def check_against_last_report(contact):
    """
        Check if the report manager is not outdated and is initialized 
        properly
    """
    
    try:
        report_manager = Report.objects.filter(status__contact=contact.pk)\
                                       .latest('updated')
    except Report.DoesNotExist:
        is_outdated = True
    else:
        is_outdated = report_manager.is_outdated()
    
    if is_outdated:
        raise ExitHandle(_(u"You must specify the campaign and location you "\
                           u"are reporting for. Send 'VIL' first."))
                       
    if not report_manager.status.vil:
        raise ExitHandle(_(u"You must specify the population of the location "\
                           u"your are reporting for. Send a complete "\
                           u"population report with 'VIL' first."))
                           
    return report_manager


def rowdata_to_excel(data):

    ''' returns an excel-file buffer containing results for a campaign '''

    timesb = Font()
    timesb.name = 'Times New Roman'
    timesb.bold = True

    header = easyxf("font: bold on, height 210; align: rota 90")

    regular = XFStyle()

    wb = Workbook(encoding='utf-8')
    ws0 = wb.add_sheet('FILARIOSE')

    #ws0.write(0, 0, 'Village', header)
    #ws0.col(0).width = 0x0d00 * 4

    for rownum, cells in enumerate(data):

        # display header in vertical text
        if rownum == 0:
            style = header
            ws0.row(rownum).height = 0x0d00
        else:
            style = easyxf('pattern: pattern solid, fore_colour gray25;') \
                    if rownum % 2 == 0 else regular

        for i, cell in enumerate(cells):
            if i == 0:
                # large first column for location names
                ws0.col(i).width = 0x0d00 * 3
            else:
                ws0.col(i).width = 0x0d00 * 0.6
            ws0.write(rownum, i, cell, style)

    buf = StringIO()
    wb.save(buf)

    return buf.getvalue()

# todo : make that a manager method
def campaign_all_datas(campaign):

    ''' returns an array of all campaign data.

    first row contains column names string.
    Ideally we would have breaked down functions like this
    for specific topics. '''

    results = Results.completed.filter(campaign=campaign)

    def vname(field):
        return Results._meta.get_field_by_name(field)[0].verbose_name.strip()

    def child_males_treated(r):
        return r.one_dose_child_males + \
               r.two_doses_child_males + \
               r.three_doses_child_males + \
               r.four_doses_child_males

    def adult_males_treated(r):
        return r.one_dose_adult_males + \
               r.two_doses_adult_males + \
               r.three_doses_adult_males + \
               r.four_doses_adult_males

    def child_females_treated(r):
        return r.one_dose_child_females + \
               r.two_doses_child_females + \
               r.three_doses_child_females + \
               r.four_doses_child_females

    def adult_females_treated(r):
        return r.one_dose_adult_females + \
               r.two_doses_adult_females + \
               r.three_doses_adult_females + \
               r.four_doses_adult_females

    def med_received(r, di, coef=True):
        return r.stock_movements.all()[di].received

    def med_returned(r, di, coef=True):
        return r.stock_movements.all()[di].returned

    def med_used(r, di, coef=True):
        c1 = 1
        if coef:
            c2 = 2
            c3 = 3
            c4 = 4
        else:
            c1 = c2 = c3 = c4 = 1
        return \
            c1 * (r.one_dose_child_males + \
                  r.one_dose_adult_males + \
                  r.one_dose_child_females + \
                  r.one_dose_adult_females) + \
            c2 * (r.two_doses_child_males + \
                  r.two_doses_adult_males + \
                  r.two_doses_child_females + \
                  r.two_doses_adult_females) + \
            c3 * (r.three_doses_child_males + \
                  r.three_doses_adult_males + \
                  r.three_doses_child_females + \
                  r.three_doses_adult_females) + \
            c4 * (r.four_doses_child_males + \
                  r.four_doses_adult_males + \
                  r.four_doses_child_females +
                  r.four_doses_adult_females)

    def med_lost(r, di, coef=True):
        return med_received(r, di) - med_used(r, di, coef=coef) - med_returned(r, di)

    def med_lost_rate(r):
        total = med_received(r, 0) + med_received(r, 1)
        lost = med_lost(r, 0, coef=False) + med_lost(r, 1, coef=True)
        # todo: remove abs, which is a big hack to hide bad calculations
        return abs((lost * 100) / total)


    # data container
    data = []

    # Header row values
    # we could have use get_fields_with_model but I believe
    # in real life we'll want to finely control display.
    header = [\
        vname('area'),
        #vname('data_collection_location'),
        # vname('drugs_pack'),
        
        vname('total_pop'),
        vname('target_pop'),

        _(u"Programme Coverage"),
        _(u"Treated males"),
        _(u"5-15 years old treated males"),
        _(u"15+ years old treated males"),
        _(u"Treated females"),
        _(u"5-15 years old treated females"),
        _(u"15+ years old treated females"),

        _(u"Drugs loss rate"),

        _(u"Albendazole received"),
        _(u"Albendazole used"),
        _(u"Albendazole lost"),
        _(u"Albendazole returned"),

        _(u"Mectizan received"),
        _(u"Mectizan used"),
        _(u"Mectizan lost"),
        _(u"Mectizan returned"),

        vname('treated_under_six'),
        vname('one_dose_child_males'),
        vname('one_dose_adult_males'),
        vname('two_doses_child_males'),
        vname('two_doses_adult_males'),
        vname('three_doses_child_males'),
        vname('three_doses_adult_males'),
        vname('four_doses_child_males'),
        vname('four_doses_adult_males'),
        vname('one_dose_child_females'),
        vname('one_dose_adult_females'),
        vname('two_doses_child_females'),
        vname('two_doses_adult_females'),
        vname('three_doses_child_females'),
        vname('three_doses_adult_females'),
        vname('four_doses_child_females'),
        vname('four_doses_adult_females'),
        vname('child_males_not_available'),
        vname('adult_males_not_available'),
        vname('child_males_refusing'),
        vname('adult_males_refusing'),
        vname('child_males_side_effects'),
        vname('adult_males_side_effects'),
        vname('child_females_not_available'),
        vname('adult_females_not_available'),
        vname('child_females_refusing'),
        vname('adult_females_refusing'),
        vname('child_females_side_effects'),
        vname('adult_females_side_effects'),        
        vname('pregnant_child_females'),
        vname('pregnant_adult_females'),

        vname('treatment_start_date'),
        vname('treatment_end_date'),
        vname('distributor'),
    ]
    data.append(header)

    for result in results:

        row = [\

        result.area.__unicode__(),
        #result.data_collection_location.__unicode__(),
        # result.drugs_pack.__unicode__(),
        
        result.total_pop,
        result.target_pop,

        0, # _(u"Programme Coverage"),
        result.total_treated_males,
        child_males_treated(result),
        adult_males_treated(result),
        result.total_treated_females,
        child_females_treated(result),
        adult_females_treated(result),

        med_lost_rate(result),

        med_received(result, 0, coef=False),
        med_used(result, 0, coef=False),
        med_lost(result, 0, coef=False),
        med_returned(result, 0, coef=False),

        med_received(result, 1, coef=True),
        med_used(result, 1, coef=True),
        med_lost(result, 1, coef=True),
        med_returned(result, 1, coef=True),

        result.treated_under_six,
        result.one_dose_child_males,
        result.one_dose_adult_males,
        result.two_doses_child_males,
        result.two_doses_adult_males,
        result.three_doses_child_males,
        result.three_doses_adult_males,
        result.four_doses_child_males,
        result.four_doses_adult_males,
        result.one_dose_child_females,
        result.one_dose_adult_females,
        result.two_doses_child_females,
        result.two_doses_adult_females,
        result.three_doses_child_females,
        result.three_doses_adult_females,
        result.four_doses_child_females,
        result.four_doses_adult_females,
        result.child_males_not_available,
        result.adult_males_not_available,
        result.child_males_refusing,
        result.adult_males_refusing,
        result.child_males_side_effects,
        result.adult_males_side_effects,
        result.child_females_not_available,
        result.adult_females_not_available,
        result.child_females_refusing,
        result.adult_females_refusing,
        result.child_females_side_effects,
        result.adult_females_side_effects,        
        result.pregnant_child_females,
        result.pregnant_adult_females,

        result.treatment_start_date,
        result.treatment_end_date,
        result.distributor,

        ]

        data.append(row)

    return data  
