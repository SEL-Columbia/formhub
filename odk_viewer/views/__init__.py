from csv_export import csv_export
from xls_export import xls_export
from single_survey_submission import survey_responses, survey_media_files

# map view
from django.shortcuts import render_to_response
from django.template import RequestContext
import json
from odk_viewer.models import ParsedInstance


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
    points = ParsedInstance.objects.values('lat', 'lng', 'instance').filter(instance__user=request.user)
    center = {
        'lat': average([p['lat'] for p in points]),
        'lng': average([p['lng'] for p in points]),
        }
    context.points = json.dumps(list(points))
    context.center = json.dumps(center)
    return render_to_response('map.html', context_instance=context)
