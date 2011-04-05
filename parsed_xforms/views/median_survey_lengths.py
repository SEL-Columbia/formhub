from collections import defaultdict
from parsed_xforms.models import ParsedInstance
from utils import json_response
from django.shortcuts import render_to_response

def median_survey_lengths(request):
    """
    Get the median time spent on each survey.
    """
    times = defaultdict(list)
    for pi in ParsedInstance.objects.all():
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
    
