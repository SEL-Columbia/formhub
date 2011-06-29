from django.http import HttpResponse
import json

from models import LGA

def lga_data(request, lga_id):
    lga = LGA.objects.get(id=lga_id)
    json_str = json.dumps(lga.get_latest_data())
    return HttpResponse(json_str)
