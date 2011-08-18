from models import UserRequest
from django.db.models import Count
import re
from nga_districts.models import LGA
from django.template import RequestContext
from django.shortcuts import render_to_response

def user_request_counts(request):
    """
    table for managers to see TA activity on the site:

    row: user, 

    columns: user name, permission level (admin
    """
    user_request_counts = UserRequest.objects.values('user__username', 'user__email', 'path').annotate(count=Count('id'))
    regex = r'^/~([_a-z]+)$'
    # limit to lga landing pages
    user_request_counts = [urc for urc in user_request_counts if re.search(regex, urc['path'])]
    print user_request_counts
    # need to join with lgas
    lgas = dict([(lga['unique_slug'], lga) for lga in LGA.objects.values('unique_slug', 'name', 'state__name')])
    context = RequestContext(request)
    context.headers = ['State', 'LGA', 'User', 'Number of Visits']
    context.table = []
    for urc in user_request_counts:
        lga = lgas[urc['path'][2:]]
        context.table.append([lga['state__name'], lga['name'], urc['user__email'], urc['count']])
    return render_to_response("user_request_counts.html", context_instance=context)
