import json
import urllib
import urllib2
import gdata.gauth
import gdata.client
import gdata.docs.data
import gdata.docs.client

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required

from gdata.spreadsheets import client

from main.models import  TokenStorageModel
from main.views import home

token = gdata.gauth.OAuth2Token(client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    scope=', '.join(['https://docs.google.com/feeds/',
        'https://spreadsheets.google.com/feeds/']),
    user_agent='formhub')

redirect_uri = token.generate_authorize_url(
    redirect_uri=settings.GOOGLE_STEP2_URI,
    access_type='offline', approval_prompt='force')


@login_required
def google_oauth2_request(request):
    try:
        ts = TokenStorageModel.objects.get(id=request.user)
    except TokenStorageModel.DoesNotExist:
        pass
    else:
        stored_token = gdata.gauth.token_from_blob(ts.token)
        print stored_token.refresh_token, stored_token.access_token
        if stored_token.refresh_token is not None and\
           stored_token.access_token is not None:
            token.refresh_token = stored_token.refresh_token
            working_token = refresh_access_token(token, request.user)
            docs_client = client.SpreadsheetsClient(source=token.user_agent)
            docs_client = working_token.authorize(docs_client)
            docs_feed = docs_client.GetSpreadsheets()
            _l = '<ul>'
            for entry in docs_feed.entry:
                _l += '<li>%s</li>' % entry.title.text
                print entry.title.text
            _l += '</ul>'
            return HttpResponse(_l)
    print redirect_uri
    return HttpResponseRedirect(redirect_uri)


@login_required
def google_auth_return(request):
    if 'code' not in request.REQUEST:
        return HttpResponse(u"Invalid Request")
    try:
        ts = TokenStorageModel.objects.get(id=request.user)
    except TokenStorageModel.DoesNotExist:
        ts = TokenStorageModel(id=request.user)
    access_token = token.get_access_token(request.REQUEST)
    ts.token = gdata.gauth.token_to_blob(token=access_token)
    ts.save()
    return HttpResponseRedirect(reverse(home))


def refresh_access_token(token, user):
    try:
        ts = TokenStorageModel.objects.get(id=user)
    except TokenStorageModel.DoesNotExist:
        ts = TokenStorageModel(id=user)
    data = urllib.urlencode({
        'client_id': settings.GOOGLE_CLIENT_ID,
        'client_secret': settings.GOOGLE_CLIENT_SECRET,
        'refresh_token': token.refresh_token,
        'grant_type': 'refresh_token'})
    request = urllib2.Request(
        url='https://accounts.google.com/o/oauth2/token',
        data=data)
    request_open = urllib2.urlopen(request)
    response = request_open.read()
    request_open.close()
    tokens = json.loads(response)
    token.access_token = tokens['access_token']
    ts.token = gdata.gauth.token_to_blob(token)
    ts.save()
    return token
