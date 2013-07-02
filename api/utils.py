from api.models import OrganizationProfile, Team, Project

from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType


def _get_first_last_names(name):
    name_split = name.split()
    first_name = name_split[0]
    last_name = u''
    if len(name_split) > 1:
        last_name = u' '.join(name_split[1:])
    return first_name, last_name


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


def create_organization_object(org_name, creator, attrs={}):
    '''Creates an OrganizationProfile object without saving to the database'''
    name = attrs.get('name', org_name)
    first_name, last_name = _get_first_last_names(name)
    new_user = User(username=org_name, first_name=first_name,
                    last_name=last_name, email=attrs.get('email', u''))
    new_user.save()
    profile = OrganizationProfile(
        user=new_user, name=name, creator=creator,
        city=attrs.get('city', u''),
        country=attrs.get('country', u''),
        organization=attrs.get('organization', u''),
        home_page=attrs.get('home_page', u''),
        twitter=attrs.get('twitter', u''))
    return profile


def create_organization_team(organization, name, permission_names=[]):
    team = Team.objects.create(organization=organization, name=name)
    content_type = ContentType.objects.get(
        app_label='api', model='organizationprofile')
    if permission_names:
        # get permission objects
        perms = Permission.objects.filter(
            codename__in=permission_names, content_type=content_type)
        if perms:
            team.permissions.add(*tuple(perms))
    return team


def add_user_to_team(team, user):
    user.groups.add(team)


def create_organization_project(organization, project_name, created_by):
    """Creates a project for a given organization
    :param organization: User organization
    :param project_name
    :param created_by: User with permissions to create projects within the
                       organization

    :returns: a Project instance
    """
    profile = OrganizationProfile.objects.get(user=organization)
    if not profile.is_organization_owner(created_by):
        return None
    project = Project.objects.create(
        name=project_name,
        organization=organization, created_by=created_by)
    return project


def add_team_to_project(team, project):
    """Adds a  team to a project

    :param team:
    :param project:

    :returns: True if successful or project has already been added to the team
    """
    if isinstance(team, Team) and isinstance(project, Project):
        if not team.projects.filter(pk=project.pk):
            team.projects.add(project)
        return True
    return False
