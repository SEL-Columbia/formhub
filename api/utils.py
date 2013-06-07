from api.models import OrganizationProfile, Team

from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType


def create_organization(name, creator):
    """
    Organization created by a user
    - create a team, OwnerTeam with full permissions to the creator
        - Team(name='Owners', organization=organization).save()

    """
    organization = User.objects.create(username=name)
    organization_profile = OrganizationProfile.objects.create(
        user=organization, creator=creator)
    team = Team.objects.create(
        name=Team.OWNER_TEAM_NAME, organization=organization)
    content_type = ContentType.objects.get(
        app_label='api', model='organizationprofile')
    permission, created = Permission.objects.get_or_create(
        codename="is_org_owner", name="Organization Owner",
        content_type=content_type)
    team.permissions.add(permission)
    creator.groups.add(team)
    return organization_profile
