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
from utils.google import oauth2_token, get_refreshed_token, redirect_uri


def google_oauth2_request(request):
    token = None
    if request.user.is_authenticated():
        try:
            ts = TokenStorageModel.objects.get(id=request.user)
        except TokenStorageModel.DoesNotExist:
            pass
        else:
            token  = ts.token
    elif request.session.get('access_token'):
        token = request.session.get('access_token')
    if token is not None:
        stored_token = gdata.gauth.token_from_blob(token)
        if stored_token.refresh_token is not None and\
           stored_token.access_token is not None:
            oauth2_token.refresh_token = stored_token.refresh_token
            working_token = refresh_access_token(oauth2_token, request.user)
            docs_client = client.SpreadsheetsClient(source=oauth2_token.user_agent)
            docs_client = working_token.authorize(docs_client)
            docs_feed = docs_client.GetSpreadsheets()
            _l = '<ul>'
            for entry in docs_feed.entry:
                _l += '<li>%s</li>' % entry.title.text
                print entry.title.text
            _l += '</ul>'
            return HttpResponse(_l)
    return HttpResponseRedirect(redirect_uri)


def google_auth_return(request):
    if 'code' not in request.REQUEST:
        return HttpResponse(u"Invalid Request")
    if request.user.is_authenticated():
        try:
            ts = TokenStorageModel.objects.get(id=request.user)
        except TokenStorageModel.DoesNotExist:
            ts = TokenStorageModel(id=request.user)
        access_token = oauth2_token.get_access_token(request.REQUEST)
        ts.token = gdata.gauth.token_to_blob(token=access_token)
        ts.save()
    else:
        access_token = oauth2_token.get_access_token(request.REQUEST)
        request.session["access_token"] = gdata.gauth.token_to_blob(token=access_token)
    if request.session.get('google_redirect_url'):
        return HttpResponseRedirect(request.session.get('google_redirect_url'))
    return HttpResponseRedirect(reverse(home))


def refresh_access_token(token, user):
    token = get_refreshed_token(token)
    if not user.is_authenticated():
        return token
    try:
        ts = TokenStorageModel.objects.get(id=user)
    except TokenStorageModel.DoesNotExist:
        ts = TokenStorageModel(id=user)
    ts.token = gdata.gauth.token_to_blob(token)
    ts.save()
    return token
