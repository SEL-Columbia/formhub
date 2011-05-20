from collections import defaultdict
from parsed_xforms.models import ParsedInstance
from utils import json_response
from django.shortcuts import render_to_response
from deny_if_unauthorized import deny_if_unauthorized

@deny_if_unauthorized
def median_survey_lengths(request):
    """
    Get the median time spent on each survey.
    """
    times = defaultdict(list)
    for pi in ParsedInstance.objects.all().iterator():
        if pi.instance.xform:
            survey_title = pi.instance.xform.title
            if pi.end_time is not None and pi.start_time is not None:
                times[survey_title].append(pi.end_time - pi.start_time)
    for key in times.keys():
        times[key].sort()
    result = {}
    for k in times.keys():
        title_with_count = unicode(len(times[k])) + u" " + k
        result[title_with_count] = times[k][len(times[k])/2]
    return render_to_response("dict.html", {"dict":result})

@deny_if_unauthorized
def survey_lengths_for_numpy():
    times = []
    titles = []
    for pi in ParsedInstance.objects.all().iterator():
        if pi.instance.xform:
            survey_title = pi.instance.xform.title
            if survey_title not in titles: titles.append(survey_title)
            if pi.end_time is not None and pi.start_time is not None:
                delta = pi.start_time - pi.end_time
                minutes = delta.seconds/60 + delta.days*24*60
                times.append( (titles.index(survey_title), minutes) )
    return titles, times
