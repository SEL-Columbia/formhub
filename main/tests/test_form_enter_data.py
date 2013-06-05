from test_base import MainTestCase
from nose import SkipTest
from odk_logger.views import enter_data
from django.core.urlresolvers import reverse
from odk_logger.models import XForm
from main.views import set_perm, show
from main.models import MetaData
from django.conf import settings
from urlparse import urlparse
from time import time
import re
import urllib2
import urllib
import json

class TestFormEnterData(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        self._create_user_and_login()
        self._publish_transportation_form_and_submit_instance()
        self.perm_url = reverse(set_perm, kwargs={
            'username': self.user.username, 'id_string': self.xform.id_string})
        self.show_url = reverse(show,
                    kwargs={'uuid': self.xform.uuid})
        self.url = reverse(enter_data, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })

        #for enketo use only

    def _running_enketo(self):
        if hasattr(settings, 'ENKETO_URL') and \
            self._check_url(settings.ENKETO_URL):
            return True
        return False

    def test_enketo_remote_server_responses(self):
        #just in case if we want to shift the testing back to the main server
        testing_enketo_url = settings.ENKETO_URL
        #testing_enketo_url = 'http://enketo-dev.formhub.org'
        time_stamp = time()
        form_id = "test_%s" % re.sub(re.compile("\."),"_",str(time()))
        server_url = "%s/%s" % (self.base_url,self.user.username)
        enketo_url = '%slaunch/launchSurvey' % testing_enketo_url

        values = {
            'format': 'json',
            'form_id': form_id,
            'server_url' : server_url
        }
        data = urllib.urlencode(values)
        req = urllib2.Request(enketo_url, data)
        try:
            response = urllib2.urlopen(req)
            response = json.loads(response.read())
            success = response['success']
            if not success and 'reason' in response:
                fail_msg = "This enketo installation is for use by "\
                            "formhub.org users only."
                if response['reason'].startswith(fail_msg):
                    raise SkipTest
            return_url = response['url']
            success = response['success']
            self.assertTrue(success)
            enketo_base_url = urlparse(settings.ENKETO_URL).netloc
            return_base_url = urlparse(return_url).netloc
            self.assertIn(enketo_base_url, return_base_url)
        except urllib2.URLError:
            self.assertTrue(False)

        #second time
        req2 = urllib2.Request(enketo_url, data)
        try:
            response2 = urllib2.urlopen(req2)
            response2 = json.loads(response2.read())
            return_url_2 = response2['url']
            success2 = response2['success']
            reason2 = response2['reason']
            self.assertEqual(return_url, return_url_2)
            self.assertFalse(success2)
            self.assertEqual(reason2, "existing")
        except urllib2.URLError:
            self.assertTrue(False)

        #error message
        values['server_url']=""
        data = urllib.urlencode(values)
        req3 = urllib2.Request(enketo_url, data)
        try:
            response3 = urllib2.urlopen(req3)
            response3 = json.loads(response3.read())
            success3 = response3['success']
            reason3 = response3['reason']
            self.assertFalse(success3)
            self.assertEqual(reason3, "empty")
        except urllib2.URLError:
            self.assertTrue(False)



    def test_running_enketo(self):
        exist = self._running_enketo()
        self.assertTrue(exist)

    def test_enter_data_redir(self):
        response = self.client.get(self.url)
        #make sure response redirect to an enketo site
        enketo_base_url = urlparse(settings.ENKETO_URL).netloc
        redirected_base_url = urlparse(response['Location']).netloc
        #TODO: checking if the form is valid on enketo side
        self.assertIn(enketo_base_url, redirected_base_url)
        self.assertEqual(response.status_code, 302)

    def test_enter_data_no_permission(self):
        response = self.anon.get(self.url)
        status_code = 200 if self._running_enketo() else 403
        self.assertEqual(response.status_code, 403)

    def test_public_with_link_to_share_toggle_on(self):
        #sharing behavior as of 09/13/2012:
        #it requires both data_share and form_share both turned on
        #in order to grant anon access to form uploading
        #TODO: findout 'for_user': 'all' and what it means
        response = self.client.post(self.perm_url, {'for_user': 'all',
            'perm_type': 'link'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(MetaData.public_link(self.xform), True)
        #toggle shared on
        self.xform.shared = True
        self.xform.shared_data = True
        self.xform.save()
        response = self.anon.get(self.show_url)
        self.assertEqual(response.status_code, 302)
        response = self.anon.get(self.url)
        status_code = 302 if self._running_enketo() else 403
        self.assertEqual(response.status_code, status_code)


    def test_enter_data_non_existent_user(self):
        url = reverse(enter_data, kwargs={
            'username': 'nonexistentuser',
            'id_string': self.xform.id_string
        })
        response = self.anon.get(url)
        self.assertEqual(response.status_code, 404)
