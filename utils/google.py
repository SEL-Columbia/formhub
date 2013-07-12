import json

import urllib
import urllib2

import gdata
import gdata.gauth
import gdata.docs
import gdata.data
import gdata.docs.client
import gdata.docs.data

from django.conf import settings

oauth2_token = gdata.gauth.OAuth2Token(
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    scope=' '.join(
        ['https://docs.google.com/feeds/',
            'https://spreadsheets.google.com/feeds/']),
    user_agent='formhub')

redirect_uri = oauth2_token.generate_authorize_url(
    redirect_uri=settings.GOOGLE_STEP2_URI,
    access_type='offline', approval_prompt='force')


def get_refreshed_token(token):
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
    return token


def google_export_xls(filename, title, token, blob=True):
    if blob:
        token = gdata.gauth.token_from_blob(token)
    if token.refresh_token is not None \
            and token.access_token is not None:
        oauth2_token.refresh_token = token.refresh_token
        working_token = get_refreshed_token(oauth2_token)
        docs_client = gdata.docs.client.DocsClient(
            source=oauth2_token.user_agent)
        docs_client = working_token.authorize(docs_client)
        xls_doc = gdata.docs.data.Resource(
            type='spreadsheet', title=title)
        media = gdata.data.MediaSource()
        media.SetFileHandle(filename, 'application/vnd.ms-excel')
        xls_doc = docs_client.CreateResource(xls_doc, media=media)
        return xls_doc.find_html_link()
