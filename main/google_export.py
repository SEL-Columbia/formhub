import json
import urllib
import urllib2
import gdata.gauth
import gdata.client
import gdata.docs.data
import gdata.docs.client

from django.conf import settings
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required

from gdata.spreadsheets import client

from main.models import  TokenStorageModel

token = gdata.gauth.OAuth2Token(client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    scope='https://docs.google.com/feeds/ https://spreadsheets.google.com/feeds/',
    user_agent='formhub'
)

redirect_uri = token.generate_authorize_url(
    redirect_uri=settings.GOOGLE_STEP2_URI,
    access_type='offline'
)

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
            token.access_token = refresh_access_token(stored_token.refresh_token)
            token.refresh_token = stored_token.refresh_token
            print stored_token.refresh_token, stored_token.access_token
            docs_client = client.SpreadsheetsClient(source=token.user_agent)
            docs_client = token.authorize(docs_client)
            docs_feed = docs_client.GetSpreadsheets()
            _l = '<ul>'
            for entry in docs_feed.entry:
                _l += '<li>%s</li>' % entry.title.text
                print entry.title.text
            _l += '</ul>'
            # save token with new access_token
            ts.token = gdata.gauth.token_to_blob(token)
            ts.save()
            return HttpResponse(_l)
    print redirect_uri
    return HttpResponseRedirect(redirect_uri)


@login_required
def google_auth_return(request):
    try:
        ts = TokenStorageModel.objects.get(id=request.user)
    except TokenStorageModel.DoesNotExist:
        ts = TokenStorageModel(id=request.user)
    access_token = token.get_access_token(request.REQUEST)
    ts.token = gdata.gauth.token_to_blob(token=access_token)
    ts.save()
    return HttpResponseRedirect('/gauth')


def refresh_access_token(refresh_token):
    data = urllib.urlencode({
        'client_id': settings.GOOGLE_CLIENT_ID,
        'client_secret': settings.GOOGLE_CLIENT_SECRET,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'})
    request = urllib2.Request(
        url='https://accounts.google.com/o/oauth2/token',
        data=data)
    request_open = urllib2.urlopen(request)
    response = request_open.read()
    request_open.close()
    print response
    tokens = json.loads(response)
    access_token = tokens['access_token']
    return access_token