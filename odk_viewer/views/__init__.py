#booo (import *)
from old_views import *

from dashboard_views import dashboard, state_count_json

from csv_export import csv_export
from xls_export import xls_export
from single_survey_submission import survey_responses, survey_media_files


from django.shortcuts import render_to_response
from django.template import RequestContext
import json


def average(values):
    return sum(values, 0.0) / len(values)


def table():
    return """
<table class="zebra-striped"> 
    <thead> 
      <tr> 
        <th>Title</th> 
        <th>ID</th> 
        <th>Downloadable</th> 
        <th>Number of Submissions</th> 
        <th>Time of Last Submission</th> 
        <th>Export</th> 
      </tr> 
    </thead> 
    <tbody> 
      
      <tr> 
        <td>text_and_integer</td> 
        <td>text_and_integer</td> 
        <td> 
	  <a href="/admin/text_and_integer/toggle_downloadable/?next=/"> 
	    
	    [ yes ]
	    
	  </a> 
        </td> 
        <td>9</td> 
        <td> 
	  
	  Sept. 23, 2011, 10:59 a.m.
	  
        </td> 
        <td> 
          <a href="/odk_viewer/export_spreadsheet/text_and_integer.csv">csv</a>,
          <a href="/odk_viewer/export_spreadsheet/text_and_integer.xls">xls</a> 
        </td> 
      </tr> 
      
    </tbody> 
  </table>
"""


def map(request):
    context = RequestContext(request)
    points = [[40, 40], [40, 41], [41, 40], [41, 41]]
    center = [average([p[0] for p in points]),
              average([p[1] for p in points])]
    for i in range(len(points)):
        points[i].append(table())
    points = [dict(zip(['lat', 'lng', 'info'], p)) for p in points]
    context.points = json.dumps(points)
    context.center = json.dumps({'lat': center[0], 'lng': center[1]})
    return render_to_response('map.html', context_instance=context)
