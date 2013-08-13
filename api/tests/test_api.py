import json

from django.test import TestCase
from django.test import RequestFactory

from django.contrib.auth.models import User
from django.contrib.auth.models import Permission

from api.models import OrganizationProfile
from api.views import OrgProfileViewSet


class TestAPICase(TestCase):

    def setUp(self):
        super(TestAPICase, self).setUp()
        self.factory = RequestFactory()
        self._login_user_and_profile()

    def _set_api_permissions(self, user):
        add_userprofile = Permission.objects.get(
            content_type__app_label='main', content_type__model='userprofile',
            codename='add_userprofile')
        user.user_permissions.add(add_userprofile)

    def _login_user_and_profile(self, extra_post_data={}):
        post_data = {
            'username': 'bob',
            'email': 'bob@columbia.edu',
            'password1': 'bobbob',
            'password2': 'bobbob',
            'name': 'Bob',
            'city': 'Bobville',
            'country': 'US',
            'organization': 'Bob Inc.',
            'home_page': 'bob.com',
            'twitter': 'boberama'
        }
        url = '/accounts/register/'
        post_data = dict(post_data.items() + extra_post_data.items())
        self.response = self.client.post(url, post_data)
        try:
            self.user = User.objects.get(username=post_data['username'])
        except User.DoesNotExist:
            pass
        else:
            self.user.is_active = True
            self.user.save()
            self.assertTrue(
                self.client.login(username=self.user.username,
                                  password='bobbob'))
            self.extra = {
                'HTTP_AUTHORIZATION': 'Token %s' % self.user.auth_token}
            self._set_api_permissions(self.user)

    def _org_create(self):
        view = OrgProfileViewSet.as_view({
            'get': 'list',
            'post': 'create'
        })
        request = self.factory.get('/', **self.extra)
        response = view(request)
        self.assertEqual(response.status_code, 200)
        data = {
            'org': u'denoinc',
            'name': u'Dennis',
            # 'email': u'info@deno.com',
            'city': u'Denoville',
            'country': u'US',
            #'organization': u'Dono Inc.',
            'home_page': u'deno.com',
            'twitter': u'denoinc',
            'description': u'',
            'address': u'',
            'phonenumber': u'',
            'require_auth': False,
            # 'password': 'denodeno',
        }
        # response = self.client.post(
        request = self.factory.post(
            '/', data=json.dumps(data),
            content_type="application/json", **self.extra)
        response = view(request)
        self.assertEqual(response.status_code, 201)
        data['url'] = 'http://testserver/api/v1/orgs/denoinc'
        data['user'] = 'http://testserver/api/v1/users/denoinc'
        data['creator'] = 'http://testserver/api/v1/users/bob'
        self.assertEqual(response.data, data)
        self.company_data = response.data
        self.organization = OrganizationProfile.objects.get(
            user__username=data['org'])
