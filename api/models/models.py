from django.db import models
from django.contrib.auth.models import User, Permission, Group
from django.contrib.contenttypes.models import ContentType

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


class Project(models.Model):
    pass


class Team(Group):
    """
    - They belong to an organization
    - They have members
    - They have access to projects
    - should this be a django group - permissions?
    - @name
    - @organization
    - @members
    - @projects
    """

    class Meta:
        app_label = 'api'

    OWNER_TEAM_NAME = "Owners"

    def __unicode__(self):
        # return a clear group name without username to user for viewing
        return self.name.split('#')[1]

    organization = models.ForeignKey(User)
    projects = models.ManyToManyField(Project)

    def save(self, *args, **kwargs):
        # allow use of same name in different organizations/users
        # concat with #
        self.name = u'%s#%s' % (self.organization.username, self.name)
        super(Team, self).save(*args, **kwargs)
