from django.db import models
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save

from main.models import UserProfile
from odk_logger.models import XForm


class OrganizationProfile(UserProfile):
    """Organization: Extends the user profile for organization specific info

        * What does this do?
            - it has a createor
            - it has owner(s), through permissions/group
            - has members, through permissions/group
            - no login access, no password? no registration like a normal user?
            - created by a user who becomes the organization owner
        * What relationships?
    """

    class Meta:
        app_label = 'api'

    is_organization = models.BooleanField(default=True)
    # Other fields here
    creator = models.ForeignKey(User)

    def save(self, *args, **kwargs):
        super(OrganizationProfile, self).save(*args, **kwargs)

    def remove_user_from_organization(self, user):
        """Remove's a user from all teams/groups in the organization
        """
        for group in user.groups.filter('%s#' % self.user.username):
            user.groups.remove(group)

    def is_organization_owner(self, user):
        """Checks if user is in the organization owners team

        :param user: User to check

        :returns: Boolean whether user has organization level permissions
        """
        has_owner_group = user.groups.filter(
            name='%s#%s' % (self.user.username, Team.OWNER_TEAM_NAME))
        return True if has_owner_group else False


def create_owner_team_and_permissions(sender, instance, created, **kwargs):
        if created:
            team = Team.objects.create(
                name=Team.OWNER_TEAM_NAME, organization=instance.user)
            content_type = ContentType.objects.get(
                app_label='api', model='organizationprofile')
            permission, created = Permission.objects.get_or_create(
                codename="is_org_owner", name="Organization Owner",
                content_type=content_type)
            team.permissions.add(permission)
            instance.creator.groups.add(team)
post_save.connect(
    create_owner_team_and_permissions, sender=OrganizationProfile,
    dispatch_uid='create_owner_team_and_permissions')


class Project(models.Model):
    class Meta:
        app_label = 'api'
        unique_together = (('name', 'organization'),)

    name = models.CharField(max_length=255)
    organization = models.ForeignKey(User, related_name='project_organization')
    created_by = models.ForeignKey(User, related_name='project_creator')

    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u'%s|%s' % (self.organization, self.name)


class Team(Group):
    """
    TODO: documentation
    TODO: Whenever a member is removed from members team,
          we  should remove them from all teams and projects
          within the organization.
    """
    class Meta:
        app_label = 'api'

    OWNER_TEAM_NAME = "Owners"

    organization = models.ForeignKey(User)
    projects = models.ManyToManyField(Project)

    def __unicode__(self):
        # return a clear group name without username to user for viewing
        return self.name.split('#')[1]

    @property
    def team_name(self):
        return self.__unicode__()

    def save(self, *args, **kwargs):
        # allow use of same name in different organizations/users
        # concat with #
        if not self.name.startswith('#'.join([self.organization.username])):
            self.name = u'%s#%s' % (self.organization.username, self.name)
        super(Team, self).save(*args, **kwargs)


class ProjectXForm(models.Model):
    xform = models.ForeignKey(XForm)
    project = models.ForeignKey(Project)
    created_by = models.ForeignKey(User)

    class Meta:
        app_label = 'api'
        unique_together = ('xform', 'project')
