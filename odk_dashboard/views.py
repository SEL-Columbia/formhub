from django.shortcuts import render_to_response
from django.db.models import Avg, Max, Min, Count
from django.http import HttpResponse
from odk_dropbox import utils
from .models import ParsedSubmission

def dashboard(request):
    return render_to_response('dashboard.html')

def submission_counts(request):
    s = ParsedSubmission.objects.values("survey_type").annotate(Count("survey_type"))
    return render_to_response("submission_counts.html",
                              {"submission_counts" : s})

def csv(request, survey_type):
    pss = ParsedSubmission.objects.filter(survey_type=survey_type)
    handlers = [utils.parse_submission(ps.submission) for ps in pss]
    dicts = [handler.get_dict() for handler in handlers]
    itemss = [utils.flatten_dict(d) for d in dicts]
    flattened_dicts = [dict(items) for items in itemss]    
    table = utils.table(flattened_dicts)
    return HttpResponse(utils.csv(table), mimetype="application/csv")
