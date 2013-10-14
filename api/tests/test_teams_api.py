import json

from api.tests.test_api import TestAPICase

from api.models import Team
from api.views import TeamViewSet


class TestTeamsAPI(TestAPICase):
    def setUp(self):
        super(TestTeamsAPI, self).setUp()
        self.view = TeamViewSet.as_view({
            'get': 'list',
            'post': 'create'
        })

    def test_teams_list(self):
        self._team_create()
        request = self.factory.get('/', **self.extra)
        response = self.view(request)
        owner_team = {
            'url':
            'http://testserver/api/v1/teams/denoinc/%s' % self.owner_team.pk,
            'name': u'Owners',
            'organization': 'http://testserver/api/v1/users/denoinc',
            'projects': []}
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [owner_team, self.team_data])

    def test_teams_get(self):
        self._team_create()
        view = TeamViewSet.as_view({
            'get': 'retrieve'
        })
        request = self.factory.get('/', **self.extra)
        response = view(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data,
                         {'detail':
                          'Expected URL keyword argument `owner` and `pk`.'})
        request = self.factory.get('/', **self.extra)
        response = view(request, owner='denoinc', pk=self.team.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, self.team_data)

    def _team_create(self):
        self._org_create()
        data = {
            'name': u'dreamteam',
            'organization': self.company_data['user']
        }
        request = self.factory.post(
            '/', data=json.dumps(data),
            content_type="application/json", **self.extra)
        response = self.view(request, owner='denoinc')
        self.assertEqual(response.status_code, 201)
        self.owner_team = Team.objects.get(
            organization=self.organization.user,
            name='%s#Owners' % (self.organization.user.username))
        team = Team.objects.get(
            organization=self.organization.user,
            name='%s#%s' % (self.organization.user.username, data['name']))
        data['url'] = 'http://testserver/api/v1/teams/denoinc/%s' % team.pk
        self.assertDictContainsSubset(data, response.data)
        self.team_data = response.data
        self.team = team

    def test_teams_create(self):
        self._team_create()
