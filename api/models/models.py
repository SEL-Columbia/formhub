from django.db import models
from django.contrib.auth.models import User, Group

from main.models import UserProfile


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


class Project(models.Model):
    """
    - @name
    - belongs to an organization
    - @creator
    - @teams - permissions?
    - its own team?

    Larry owns modlabs organization
    Larry creates a project 'atasoils' to modilabs
    - create a project  ata_soils
        - name = ata_soils
        - creator = larry
        - who has access to atasoils?
        - do we add a team to atasoils?
        - do we have a atasoils project team auto created?
    """


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

    def save(self, *args, **kwargs):
        # allow use of same name in different organizations/users
        # concat with #
        self.name = u'%s#%s' % (self.organization.username, self.name)
        super(Team, self).save(*args, **kwargs)
