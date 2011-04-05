import json
from bson import json_util
from django.http import HttpResponse

def json_response(pyobj):
    json_str = json.dumps(pyobj, default=json_util.default)
    return HttpResponse(json_str)
