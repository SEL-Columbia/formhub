from django.contrib.auth.models import Permission
from main.tests.test_base import MainTestCase
from api.models import Team, OrganizationProfile, Project
from api.utils import create_organization, add_user_to_team
from api.utils import create_organization_team
from api.utils import create_organization_project


class TestModels(MainTestCase):
    def test_create_organization_creates_team_and_perms(self):
        # create a user - bob
        profile = create_organization("modilabs", self.user)
        self.assertIsInstance(profile, OrganizationProfile)
        organization_profile = OrganizationProfile.objects.get(
            user__username="modilabs")

        # check organization was created
        self.assertTrue(organization_profile.is_organization)

        # check that the default team was created
        team_name = "modilabs#%s" % Team.OWNER_TEAM_NAME
        team = Team.objects.get(
            organization=organization_profile.user, name=team_name)
        self.assertIsInstance(team, Team)
        self.assertIn(team.group_ptr, self.user.groups.all())
        self.assertTrue(self.user.has_perm('api.is_org_owner'))

    def test_create_organization_team(self):
        profile = create_organization("modilabs", self.user)
        organization = profile.user
        team_name = 'dev'
        perms = ['is_org_owner', ]
        create_organization_team(organization, team_name, perms)
        team_name = "modilabs#%s" % team_name
        dev_team = Team.objects.get(organization=organization, name=team_name)
        self.assertIsInstance(dev_team, Team)
        self.assertIsInstance(
            dev_team.permissions.get(codename='is_org_owner'), Permission)

    def _create_organization(self, org_name, user):
        profile = create_organization(org_name, user)
        self.organization = profile.user
        return self.organization

    def test_assign_user_to_team(self):
        # create the organization
        organization = self._create_organization("modilabs", self.user)
        user_deno = self._create_user('deno', 'deno')

        # create another team
        team_name = 'managers'
        team = create_organization_team(organization, team_name)
        add_user_to_team(team, user_deno)
        self.assertIn(team.group_ptr, user_deno.groups.all())

    def _create_project(iself, organization, project_name, user):
        project = create_organization_project(
            organization, project_name, user)
        return project

    def test_create_organization_project(self):
        organization = self._create_organization("modilabs", self.user)
        project_name = "demo"
        project = self._create_project(organization, project_name, self.user)
        self.assertIsInstance(project, Project)
        self.assertEqual(project.name, project_name)

        user_deno = self._create_user('deno', 'deno')
        project = create_organization_project(
            organization, project_name, user_deno)
        self.assertIsNone(project)
