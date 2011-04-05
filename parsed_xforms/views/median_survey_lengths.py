from collections import defaultdict
from parsed_xforms.models import ParsedInstance
from utils import json_response
from django.shortcuts import render_to_response

def median_survey_lengths(request):
    """
    Get the median time spent on each survey.
    """
    times = defaultdict(list)
    for pi in ParsedInstance.objects.all().iterator():
        if pi.instance.xform:
            survey_title = pi.instance.xform.title
            times[survey_title].append(pi.end_time - pi.start_time)
    for key in times.keys():
        times[key].sort()
    result = {}
    for k in times.keys():
        result[k] = (times[k][len(times[k])/2], len(times[k]))
    return render_to_response("dict.html", {"dict":result})
    
