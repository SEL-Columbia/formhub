from django.db import IntegrityError
from django.contrib.auth.models import Permission
from main.tests.test_base import MainTestCase
from api.models import Team, OrganizationProfile, Project, ProjectXForm
from api import utils


class TestModels(MainTestCase):
    def test_create_organization_creates_team_and_perms(self):
        # create a user - bob
        profile = utils.create_organization("modilabs", self.user)
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
        profile = utils.create_organization("modilabs", self.user)
        organization = profile.user
        team_name = 'dev'
        perms = ['is_org_owner', ]
        utils.create_organization_team(organization, team_name, perms)
        team_name = "modilabs#%s" % team_name
        dev_team = Team.objects.get(organization=organization, name=team_name)
        self.assertIsInstance(dev_team, Team)
        self.assertIsInstance(
            dev_team.permissions.get(codename='is_org_owner'), Permission)

    def _create_organization(self, org_name, user):
        profile = utils.create_organization(org_name, user)
        self.organization = profile.user
        return self.organization

    def test_assign_user_to_team(self):
        # create the organization
        organization = self._create_organization("modilabs", self.user)
        user_deno = self._create_user('deno', 'deno')

        # create another team
        team_name = 'managers'
        team = utils.create_organization_team(organization, team_name)
        utils.add_user_to_team(team, user_deno)
        self.assertIn(team.group_ptr, user_deno.groups.all())

    def _create_project(iself, organization, project_name, user):
        project = utils.create_organization_project(
            organization, project_name, user)
        return project

    def test_create_organization_project(self):
        organization = self._create_organization("modilabs", self.user)
        project_name = "demo"
        project = self._create_project(organization, project_name, self.user)
        self.assertIsInstance(project, Project)
        self.assertEqual(project.name, project_name)

        user_deno = self._create_user('deno', 'deno')
        project = utils.create_organization_project(
            organization, project_name, user_deno)
        self.assertIsNone(project)

    def test_add_team_to_project(self):
        organization = self._create_organization("modilabs", self.user)
        project_name = "demo"
        team_name = "enumerators"
        project = self._create_project(organization, project_name, self.user)
        team = utils.create_organization_team(organization, team_name)
        result = utils.add_team_to_project(team, project)
        self.assertTrue(result)
        self.assertIn(project, team.projects.all())

    def test_add_form_to_project(self):
        organization = self._create_organization("modilabs", self.user)
        project_name = "demo"
        project = self._create_project(organization, project_name, self.user)
        self._publish_transportation_form()
        count = ProjectXForm.objects.count()
        project_xform = utils.add_xform_to_project(
            self.xform, project, self.user)
        self.assertEqual(ProjectXForm.objects.count(), count + 1)
        self.assertIsInstance(project_xform, ProjectXForm)
        with self.assertRaises(IntegrityError):
            utils.add_xform_to_project(
                self.xform, project, self.user)
