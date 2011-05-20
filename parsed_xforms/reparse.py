#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from xform_manager.models import Instance, XForm
from parsed_xforms.models import ParsedInstance, Registration
from nga_districts import models as nga_models
from surveyor_manager.models import Surveyor

from django.contrib.auth.models import User
from django.conf import settings

xform_db = settings.MONGO_DB
xform_instances = xform_db.instances

import time, math

def get_counts():
    cols = ['instances', 'parsed_instances', 'mongo_instances', \
            'districts_assigned', 'districts_total', 'registrations', 'surveyors', 'users']
    counts = {
        'instances': Instance.objects.count(),
        'parsed_instances': ParsedInstance.objects.count(),
        'districts_assigned': ParsedInstance.objects.exclude(lga=None).count(),
        'districts_total': nga_models.LGA.objects.count(),
        'registrations': Registration.objects.count(),
        'mongo_instances': xform_instances.count(),
        'surveyors': Surveyor.objects.count(),
        'users': User.objects.count()
    }
    return (cols, counts, time.clock())

def reparse_all(*args, **kwargs):
    debug = kwargs.get('debug', False)
    
    if debug:
        print "[Reparsing XForm Instances]\n"
        sim_reset = kwargs.get('reset', False)
        if sim_reset:
            print " --> %s" % reset_values.__doc__.strip()
            reset_values()
        
        cols, counts_1, start_time = get_counts()

    # Delete all parsed instances.
    ParsedInstance.objects.all().delete()
    for i in Instance.objects.all().iterator():
        # There are a few instances that throw errors
        try:
            ParsedInstance.objects.create(instance=i)
        except Exception as e:
            print e
    
    if debug:
        cols, counts_2, end_time = get_counts()
        print "That process took [%d ticks]" % math.floor(1000 * (end_time-start_time))
        display_counts_as_table(cols, [counts_1, counts_2])


def display_counts_as_table(cols, list_of_dicts):
    strs = [[] for row in list_of_dicts]
    col_heads = []
    breaker = []
    for c in cols:
        col_heads.append(" %-19s" % c)
        breaker.append("--------------------")
        for i in range(0, len(list_of_dicts)):
            strs[i].append(" %-18d " % list_of_dicts[i][c])
    
    print '|'.join(col_heads)
    print '-'.join(breaker)
    for starr in strs:
        print '|'.join(starr)

#        strs[1].append(" %-18d " % cts_1[c])
#        strs[2].append(" %-18d " % cts_2[c])
#        strs[3].append("--------------------")
    
#    print '|'.join(strs[0])
#    print '-'.join(strs[3])
#    print '|'.join(strs[1])
#    print '|'.join(strs[2])
#    print "\n"
    
    
def reset_values():
    """
    This function is meant to simulate what we want to acheive with i.delete(). Right now, it is resetting mongo_db, Deleting ParsedInstances, Deleting Surveyors.
    """
    try:
        xform_db.instances.drop()
    except Exception, e:
        #i can't believe i'm doing this, but
        # it seems to be the only way to get this to not fail
        # every other time i run it.
        xform_db.instances.drop()
    
    for x in Instance.objects.all():
        pi = ParsedInstance.objects.filter(instance=x)
        if pi.count() > 0:
            x.parsed_instance.delete()
    for s in Surveyor.objects.all(): s.delete()
    return reset_stuff.__doc__.strip()
