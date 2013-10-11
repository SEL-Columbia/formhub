import os
import json
from django.conf import settings

from django.test import TestCase
from django.test import RequestFactory

from django.contrib.auth.models import User
from django.contrib.auth.models import Permission

from utils.user_auth import set_api_permissions_for_user

from api.models import OrganizationProfile, Project
from api.views import OrgProfileViewSet
from api.views import ProjectViewSet
from api.serializers import ProjectSerializer


class TestAPICase(TestCase):

    def setUp(self):
        super(TestAPICase, self).setUp()
        self.factory = RequestFactory()
        self._login_user_and_profile()
        self.maxDiff = None

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
            set_api_permissions_for_user(self.user)

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

    def _project_create(self):
        view = ProjectViewSet.as_view({
            'post': 'create'
        })
        data = {
            'name': u'demo',
            'owner': 'http://testserver/api/v1/users/bob'
        }
        request = self.factory.post(
            '/', data=json.dumps(data),
            content_type="application/json", **self.extra)
        response = view(request, owner='bob')
        self.assertEqual(response.status_code, 201)
        self.project = Project.objects.filter(name=data['name'])[0]
        data['url'] = 'http://testserver/api/v1/projects/bob/%s'\
            % self.project.pk
        self.assertDictContainsSubset(data, response.data)
        self.project_data = ProjectSerializer(
            self.project, context={'request': request}).data

    def _publish_xls_form_to_project(self):
        self._project_create()
        view = ProjectViewSet.as_view({
            'post': 'forms'
        })
        project_id = self.project.pk
        data = {
            'owner': 'http://testserver/api/v1/users/bob',
            'public': False,
            'public_data': False,
            'description': u'',
            'downloadable': True,
            'is_crowd_form': False,
            'allows_sms': False,
            'encrypted': False,
            'sms_id_string': u'transportation_2011_07_25',
            'id_string': u'transportation_2011_07_25',
            'title': u'transportation_2011_07_25',
            'bamboo_dataset': u''
        }
        path = os.path.join(
            settings.PROJECT_ROOT, "main", "tests", "fixtures",
            "transportation", "transportation.xls")
        with open(path) as xls_file:
            post_data = {'xls_file': xls_file}
            request = self.factory.post('/', data=post_data, **self.extra)
            response = view(request, owner='bob', pk=project_id)
            self.assertEqual(response.status_code, 201)
            self.xform = self.user.xforms.all()[0]
            data.update({
                'url':
                'http://testserver/api/v1/forms/bob/%s' % self.xform.pk
            })
            self.assertDictContainsSubset(data, response.data)
            self.form_data = response.data
