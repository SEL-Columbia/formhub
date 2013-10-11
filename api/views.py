import json

from django import forms
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from django.contrib.contenttypes.models import ContentType

from rest_framework import viewsets
from rest_framework import exceptions
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.decorators import action
from rest_framework.settings import api_settings
from rest_framework.renderers import BaseRenderer

from taggit.forms import TagField

from api import serializers as api_serializers
from api import mixins
from api.signals import xform_tags_add, xform_tags_delete
from api import tools as utils

from utils.user_auth import check_and_set_form_by_id
from main.models import UserProfile

from odk_logger.models import XForm, Instance
from odk_viewer.models import ParsedInstance

from api.models import Project, OrganizationProfile, ProjectXForm, Team


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This endpoint allows you to list and retrieve user's first and last names.

    ## List Users
    > Example
    >
    >       curl -X GET https://formhub.org/api/v1/users

    > Response:

    >       [
    >            {
    >                "username": "demo",
    >                "first_name": "First",
    >                "last_name": "Last"
    >            },
    >            {
    >                "username": "another_demo",
    >                "first_name": "Another",
    >                "last_name": "Demo"
    >            },
    >            ...
    >        ]


    ## Retrieve a specific user info

    <pre class="prettyprint"><b>GET</b> /api/v1/users/{username}</pre>

    > Example:
    >
    >        curl -X GET https://formhub.org/api/v1/users/demo

    > Response:
    >
    >       {
    >           "username": "demo",
    >           "first_name": "First",
    >           "last_name": "Last"
    >       }

    """
    queryset = User.objects.all()
    serializer_class = api_serializers.UserSerializer
    lookup_field = 'username'
    permission_classes = [permissions.DjangoModelPermissions, ]

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous():
            user = User.objects.get(pk=-1)
        return User.objects.filter(
            Q(pk__in=user.userprofile_set.values('user')) | Q(pk=user.pk))


class UserProfileViewSet(mixins.ObjectLookupMixin, viewsets.ModelViewSet):
    """
    List, Retrieve, Update, Create/Register users.

    ## Register a new User
    <pre class="prettyprint"><b>POST</b> /api/v1/profiles</pre>
    > Example
    >
    >        {
    >            "username": "demo",
    >            "name": "Demo User",
    >            "email": "demo@localhost.com",
    >            "city": "Kisumu",
    >            "country": "KE",
    >            ...
    >        }

    ## List User Profiles
    <pre class="prettyprint"><b>GET</b> /api/v1/profiles</pre>
    > Example
    >
    >       curl -X GET https://formhub.org/api/v1/profiles

    > Response
    >
    >       [
    >        {
    >            "url": "https://formhub.org/api/v1/profiles/demo",
    >            "username": "demo",
    >            "name": "Demo User",
    >            "email": "demo@localhost.com",
    >            "city": "",
    >            "country": "",
    >            "organization": "",
    >            "website": "",
    >            "twitter": "",
    >            "gravatar": "https://secure.gravatar.com/avatar/xxxxxx",
    >            "require_auth": false,
    >            "user": "https://formhub.org/api/v1/users/demo"
    >        },
    >        {
    >           ...}, ...
    >       ]

    ## Retrieve User Profile Information

    <pre class="prettyprint"><b>GET</b> /api/v1/profiles/{username}</pre>
    > Example
    >
    >       curl -X GET https://formhub.org/api/v1/profiles/demo

    > Response
    >
    >        {
    >            "url": "https://formhub.org/api/v1/profiles/demo",
    >            "username": "demo",
    >            "name": "Demo User",
    >            "email": "demo@localhost.com",
    >            "city": "",
    >            "country": "",
    >            "organization": "",
    >            "website": "",
    >            "twitter": "",
    >            "gravatar": "https://secure.gravatar.com/avatar/xxxxxx",
    >            "require_auth": false,
    >            "user": "https://formhub.org/api/v1/users/demo"
    >        }
    """
    queryset = UserProfile.objects.all()
    serializer_class = api_serializers.UserProfileSerializer
    lookup_field = 'user'
    permission_classes = [permissions.DjangoModelPermissions, ]
    ordering = ('user__username', )

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous():
            user = User.objects.get(pk=-1)
        return UserProfile.objects.filter(
            Q(user__in=user.userprofile_set.values('user')) | Q(user=user))


class OrgProfileViewSet(mixins.ObjectLookupMixin, viewsets.ModelViewSet):
    """
    List, Retrieve, Update, Create/Register Organizations

    ## Register a new Organization
    <pre class="prettyprint"><b>POST</b> /api/v1/orgs</pre>
    > Example
    >
    >        {
    >            "org": "modilabs",
    >            "name": "Modi Labs Research",
    >            "email": "modilabs@localhost.com",
    >            "city": "New York",
    >            "country": "US",
    >            ...
    >        }

    ## List of Organizations
    <pre class="prettyprint"><b>GET</b> /api/v1/orgs</pre>
    > Example
    >
    >       curl -X GET https://formhub.org/api/v1/orgs

    > Response
    >
    >       [
    >        {
    >            "url": "https://formhub.org/api/v1/orgs/modilabs",
    >            "org": "modilabs",
    >            "name": "Modi Labs Research",
    >            "email": "modilabs@localhost.com",
    >            "city": "New York",
    >            "country": "US",
    >            "website": "",
    >            "twitter": "",
    >            "gravatar": "https://secure.gravatar.com/avatar/xxxxxx",
    >            "require_auth": false,
    >            "user": "https://formhub.org/api/v1/users/modilabs"
    >            "creator": "https://formhub.org/api/v1/users/demo"
    >        },
    >        {
    >           ...}, ...
    >       ]

    ## Retrieve Organization Profile Information

    <pre class="prettyprint"><b>GET</b> /api/v1/orgs/{username}</pre>
    > Example
    >
    >       curl -X GET https://formhub.org/api/v1/orgs/modilabs

    > Response
    >
    >        {
    >            "url": "https://formhub.org/api/v1/orgs/modilabs",
    >            "org": "modilabs",
    >            "name": "Modi Labs Research",
    >            "email": "modilabs@localhost.com",
    >            "city": "New York",
    >            "country": "US",
    >            "website": "",
    >            "twitter": "",
    >            "gravatar": "https://secure.gravatar.com/avatar/xxxxxx",
    >            "require_auth": false,
    >            "user": "https://formhub.org/api/v1/users/modilabs"
    >            "creator": "https://formhub.org/api/v1/users/demo"
    >        }
    """
    queryset = OrganizationProfile.objects.all()
    serializer_class = api_serializers.OrganizationSerializer
    lookup_field = 'user'

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous():
            user = User.objects.get(pk=-1)
        return user.organizationprofile_set.all()


class SurveyRenderer(BaseRenderer):
    media_type = 'application/xml'
    format = 'xml'
    charset = 'utf-8'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data


class XFormViewSet(mixins.MultiLookupMixin, viewsets.ReadOnlyModelViewSet):
    """
List, Retrieve Published Forms.

Where:

- `owner` - is the organization or user to which the form(s) belong to.
- `pk` - is the project id
- `formid` - is the form id

## Get Form Information

<pre class="prettyprint">
<b>GET</b> /api/v1/forms/<code>{formid}</code>
<b>GET</b> /api/v1/projects/<code>{owner}</code>/<code>{pk}</code>/forms/<code>{formid}</code></pre>
> Example
>
>       curl -X GET https://formhub.org/api/v1/forms/28058

> Response
>
>       {
>           "url": "https://formhub.org/api/v1/forms/modilabs/28058",
>           "formid": 28058,
>           "uuid": "853196d7d0a74bca9ecfadbf7e2f5c1f",
>           "id_string": "Birds",
>           "sms_id_string": "Birds",
>           "title": "Birds",
>           "allows_sms": false,
>           "bamboo_dataset": "",
>           "description": "",
>           "downloadable": true,
>           "encrypted": false,
>           "is_crowd_form": false,
>           "owner": "https://formhub.org/api/v1/users/modilabs",
>           "public": false,
>           "public_data": false,
>           "date_created": "2013-07-25T14:14:22.892Z",
>           "date_modified": "2013-07-25T14:14:22.892Z"
>       }

## List Forms
<pre class="prettyprint">
<b>GET</b> /api/v1/forms
<b>GET</b> /api/v1/forms/<code>{owner}</code></pre>
> Example
>
>       curl -X GET https://formhub.org/api/v1/forms/modilabs

> Response
>
>       [{
>           "url": "https://formhub.org/api/v1/forms/modilabs/28058",
>           "formid": 28058,
>           "uuid": "853196d7d0a74bca9ecfadbf7e2f5c1f",
>           "id_string": "Birds",
>           "sms_id_string": "Birds",
>           "title": "Birds",
>           ...
>       }, ...]

## Get `JSON` | `XML` Form Representation
  <pre class="prettyprint">
  <b>GET</b> /api/v1/forms/<code>{owner}</code>/<code>{formid}</code>/form.<code>{format}</code></pre>
  > JSON Example
  >
  >       curl -X GET https://formhub.org/api/v1/forms/modilabs/28058/form.json

  > Response
  >
  >        {
  >            "name": "Birds",
  >            "title": "Birds",
  >            "default_language": "default",
  >            "id_string": "Birds",
  >            "type": "survey",
  >            "children": [
  >                {
  >                    "type": "text",
  >                    "name": "name",
  >                    "label": "1. What is your name?"
  >                },
  >                ...
  >                ]
  >        }

  > XML Example
  >
  >       curl -X GET https://formhub.org/api/v1/forms/modilabs/28058/form.xml

  > Response
  >
  >        <?xml version="1.0" encoding="utf-8"?>
  >        <h:html xmlns="http://www.w3.org/2002/xforms" ...>
  >          <h:head>
  >            <h:title>Birds</h:title>
  >            <model>
  >              <itext>
  >                 .....
  >          </h:body>
  >        </h:html>

## Get list of forms with specific tag(s)

Use the `tags` query parameter to filter the list of forms, `tags` should be a
comma separated list of tags.

  <pre class="prettyprint">
  <b>GET</b> /api/v1/forms?<code>tags</code>=<code>tag1,tag2</code>
  <b>GET</b> /api/v1/forms/<code>{owner}</code>?<code>tags</code>=<code>tag1,tag2</code></pre>

 List forms tagged `smart` or `brand new` or both.
  > Request
  >
  >       curl -X GET https://formhub.org/api/v1/forms?tag=smart,brand+new

> Response
>        HTTP 200 OK
>
>       [{
>           "url": "https://formhub.org/api/v1/forms/modilabs/28058",
>           "formid": 28058,
>           "uuid": "853196d7d0a74bca9ecfadbf7e2f5c1f",
>           "id_string": "Birds",
>           "sms_id_string": "Birds",
>           "title": "Birds",
>           ...
>       }, ...]


## Get list of Tags for a specific Form
  <pre class="prettyprint">
  <b>GET</b> /api/v1/forms/<code>{owner}</code>/<code>{formid}</code>/labels</pre>
  > Request
  >
  >       curl -X GET https://formhub.org/api/v1/forms/28058/labels

  > Response
  >
  >       ["old", "smart", "clean house"]

## Tag forms

A `POST` payload of parameter `tags` with a comma separated list of tags.

Examples

- `animal fruit denim` - space delimited, no commas
- `animal, fruit denim` - comma delimited

 <pre class="prettyprint">
  <b>POST</b> /api/v1/forms/<code>{owner}</code>/<code>{formid}</code>/labels</pre>

Payload

    {"tags": "tag1, tag2"}

## Delete a specific tag

 <pre class="prettyprint">
  <b>DELETE</b> /api/v1/forms/<code>{owner}</code>/<code>{formid}</code>/labels/<code>tag_name</code></pre>

  > Request
  >
  >       curl -X DELETE https://formhub.org/api/v1/forms/modilabs/28058/labels/tag1
  > or to delete the tag "hello world"
  >
  >       curl -X DELETE https://formhub.org/api/v1/forms/modilabs/28058/labels/hello%20world
  >
  > Response
  >
  >        HTTP 200 OK
    """
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES + [SurveyRenderer]
    queryset = XForm.objects.all()
    serializer_class = api_serializers.XFormSerializer
    lookup_fields = ('owner', 'pk')
    lookup_field = 'owner'
    extra_lookup_fields = None
    permission_classes = [permissions.DjangoModelPermissions, ]

    def get_queryset(self):
        owner = self.kwargs.get('owner', None)
        user = self.request.user
        if user.is_anonymous():
            user = User.objects.get(pk=-1)
        project_forms = []
        if owner:
            owner = get_object_or_404(User, username=owner)
            if owner != user:
                xfct = ContentType.objects.get(
                    app_label='odk_logger', model='xform')
                xfs = user.userobjectpermission_set.filter(content_type=xfct)
                user_forms = XForm.objects.filter(
                    Q(pk__in=[xf.object_pk for xf in xfs]) | Q(shared=True),
                    user=owner)\
                    .select_related('user')
            else:
                user_forms = owner.xforms.values('pk')
                project_forms = owner.projectxform_set.values('xform')
        else:
            user_forms = user.xforms.values('pk')
            project_forms = user.projectxform_set.values('xform')
        queryset = XForm.objects.filter(
            Q(pk__in=user_forms) | Q(pk__in=project_forms))
        # filter by tags if available.
        tags = self.request.QUERY_PARAMS.get('tags', None)
        if tags and isinstance(tags, basestring):
            tags = tags.split(',')
            queryset = queryset.filter(tags__name__in=tags)
        return queryset.distinct()

    @action(methods=['GET'])
    def form(self, request, format=None, **kwargs):
        if not format:
            format = 'json'
        self.object = self.get_object()
        if format == 'xml':
            data = self.object.xml
        else:
            data = json.loads(self.object.json)
        return Response(data)

    @action(methods=['GET', 'POST', 'DELETE'], extra_lookup_fields=['label', ])
    def labels(self, request, format='json', **kwargs):
        class TagForm(forms.Form):
            tags = TagField()
        status = 200
        self.object = self.get_object()
        if request.method == 'POST':
            form = TagForm(request.DATA)
            if form.is_valid():
                tags = form.cleaned_data.get('tags', None)
                if tags:
                    for tag in tags:
                        self.object.tags.add(tag)
                    xform_tags_add.send(
                        sender=XForm, xform=self.object, tags=tags)
                    status = 201
        label = kwargs.get('label', None)
        if request.method == 'GET' and label:
            data = [
                i['name']
                for i in self.object.tags.filter(name=label).values('name')]
        elif request.method == 'DELETE' and label:
            count = self.object.tags.count()
            self.object.tags.remove(label)
            xform_tags_delete.send(sender=XForm, xform=self.object, tag=label)
            # Accepted, label does not exist hence nothing removed
            if count == self.object.tags.count():
                status = 202
            data = list(self.object.tags.names())
        else:
            data = list(self.object.tags.names())
        return Response(data, status=status)


class ProjectViewSet(mixins.MultiLookupMixin,
                     mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.ListModelMixin, viewsets.GenericViewSet):
    """
List, Retrieve, Update, Create Project and Project Forms

Where:

- `owner` - is the organization to which the project(s) belong to.
- `pk` - is the project id
- `formid` - is the form id

## Register a new Organization Project
<pre class="prettyprint">
<b>POST</b> /api/v1/projects/<code>{owner}</code></pre>
> Example
>
>       {
>           "url": "https://formhub.org/api/v1/projects/modilabs/1",
>           "owner": "https://formhub.org/api/v1/users/modilabs",
>           "name": "project 1",
>           "date_created": "2013-07-24T13:37:39Z",
>           "date_modified": "2013-07-24T13:37:39Z"
>       }

## List of Organization's Projects

<pre class="prettyprint"><b>GET</b> /api/v1/projects <b>or</b>
<b>GET</b> /api/v1/projects/<code>{owner}</code></pre>
> Example
>
>       curl -X GET https://formhub.org/api/v1/projects
>       curl -X GET https://formhub.org/api/v1/projects/modilabs

> Response
>
>       [
>           {
>               "url": "https://formhub.org/api/v1/projects/modilabs/1",
>               "owner": "https://formhub.org/api/v1/users/modilabs",
>               "name": "project 1",
>               "date_created": "2013-07-24T13:37:39Z",
>               "date_modified": "2013-07-24T13:37:39Z"
>           },
>           {
>               "url": "https://formhub.org/api/v1/projects/modilabs/4",
>               "owner": "https://formhub.org/api/v1/users/modilabs",
>               "name": "project 2",
>               "date_created": "2013-07-24T13:59:10Z",
>               "date_modified": "2013-07-24T13:59:10Z"
>           }, ...
>       ]

## Retrieve Project Information

<pre class="prettyprint">
<b>GET</b> /api/v1/projects/<code>{owner}</code>/<code>{pk}</code></pre>
> Example
>
>       curl -X GET https://formhub.org/api/v1/projects/modilabs/1

> Response
>
>       {
>           "url": "https://formhub.org/api/v1/projects/modilabs/1",
>           "owner": "https://formhub.org/api/v1/users/modilabs",
>           "name": "project 1",
>           "date_created": "2013-07-24T13:37:39Z",
>           "date_modified": "2013-07-24T13:37:39Z"
>       }

## Upload XLSForm to a project

<pre class="prettyprint">
<b>GET</b> /api/v1/projects/<code>{owner}</code>/<code>{pk}</code>/forms</pre>
> Example
>
>       curl -X POST -F xls_file=@/path/to/form.xls https://formhub.org/api/v1/projects/modilabs/1/forms

> Response
>
>       {
>           "url": "https://formhub.org/api/v1/forms/28058",
>           "formid": 28058,
>           "uuid": "853196d7d0a74bca9ecfadbf7e2f5c1f",
>           "id_string": "Birds",
>           "sms_id_string": "Birds",
>           "title": "Birds",
>           "allows_sms": false,
>           "bamboo_dataset": "",
>           "description": "",
>           "downloadable": true,
>           "encrypted": false,
>           "is_crowd_form": false,
>           "owner": "modilabs",
>           "public": false,
>           "public_data": false,
>           "date_created": "2013-07-25T14:14:22.892Z",
>           "date_modified": "2013-07-25T14:14:22.892Z"
>       }

## Get Form Information for a project

<pre class="prettyprint">
<b>GET</b> /api/v1/projects/<code>{owner}</code>/<code>{pk}</code>/forms/<code>{formid}</code></pre>
> Example
>
>       curl -X GET https://formhub.org/api/v1/projects/modilabs/1/forms/28058

> Response
>
>       {
>           "url": "https://formhub.org/api/v1/forms/28058",
>           "formid": 28058,
>           "uuid": "853196d7d0a74bca9ecfadbf7e2f5c1f",
>           "id_string": "Birds",
>           "sms_id_string": "Birds",
>           "title": "Birds",
>           "allows_sms": false,
>           "bamboo_dataset": "",
>           "description": "",
>           "downloadable": true,
>           "encrypted": false,
>           "is_crowd_form": false,
>           "owner": "modilabs",
>           "public": false,
>           "public_data": false,
>           "date_created": "2013-07-25T14:14:22.892Z",
>           "date_modified": "2013-07-25T14:14:22.892Z"
>       }
    """
    queryset = Project.objects.all()
    serializer_class = api_serializers.ProjectSerializer
    lookup_fields = ('owner', 'pk')
    lookup_field = 'owner'
    extra_lookup_fields = None

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous():
            user = User.objects.get(pk=-1)
        return user.project_creator.all()

    def get_object(self, queryset=None):
        pk = self.kwargs.get('pk', None)
        if pk is not None:
            try:
                int(pk)
            except ValueError:
                raise exceptions.ParseError(
                    detail=_(u"The path parameter {pk} "
                             u"should be a number, '%s' given instead." % pk))
        return super(ProjectViewSet, self).get_object(queryset)

    def list(self, request, **kwargs):
        filter = {}
        if 'owner' in kwargs:
            filter['organization__username'] = kwargs['owner']
        # filter['created_by'] = request.user
        qs = self.get_queryset()
        qs = self.filter_queryset(qs)
        self.object_list = qs.filter(**filter)
        serializer = self.get_serializer(self.object_list, many=True)
        return Response(serializer.data)

    @action(methods=['POST', 'GET'], extra_lookup_fields=['formid', ])
    def forms(self, request, **kwargs):
        """
        POST - publish xlsform file to a specific project.

        xls_file -- xlsform file object
        """
        project = get_object_or_404(
            Project, pk=kwargs.get('pk', None),
            organization__username=kwargs.get('owner', None))
        if request.method.upper() == 'POST':
            survey = utils.publish_project_xform(request, project)
            if isinstance(survey, XForm):
                xform = XForm.objects.get(pk=survey.pk)
                serializer = api_serializers.XFormSerializer(
                    xform, context={'request': request})
                return Response(serializer.data, status=201)
            return Response(survey, status=400)
        filter = {'project': project}
        many = True
        if 'formid' in kwargs:
            many = False
            filter['xform__pk'] = int(kwargs.get('formid'))
        if many:
            qs = ProjectXForm.objects.filter(**filter)
            data = [px.xform for px in qs]
        else:
            qs = get_object_or_404(ProjectXForm, **filter)
            data = qs.xform
        serializer = api_serializers.XFormSerializer(
            data, many=many, context={'request': request})
        return Response(serializer.data)


class TeamViewSet(viewsets.ModelViewSet):
    """
This endpoint allows you to create, update and view team information.

## GET List of Teams within an Organization.
Provides a json list of teams within a specified organization
 and the projects the team is assigned to, where:

* `org` - is the unique organization name identifier

<pre class="prettyprint">
  <b>GET</b> /api/v1/teams
  <b>GET</b> /api/v1/teams/<code>{org}</code>
  </pre>

  > Example
  >
  >       curl -X GET https://formhub.org/api/v1/teams/bruize

  > Response
  >
  >        [
  >            {
  >                "url": "https://formhub.org/api/v1/teams/bruize/1",
  >                "name": "Owners",
  >                "organization": "https://formhub.org/api/v1/users/bruize",
  >                "projects": []
  >            },
  >            {
  >                "url": "https://formhub.org/api/v1/teams/bruize/2",
  >                "name": "demo team",
  >                "organization": "https://formhub.org/api/v1/users/bruize",
  >                "projects": []
  >            }
  >        ]

## GET Team Info for a specific team.

Shows teams details and the projects the team is assigned to, where:

* `org` - is the unique organization name identifier
* `pk` - unique identifier for the team

<pre class="prettyprint">
  <b>GET</b> /api/v1/teams/<code>{org}</code>/<code>{pk}</code>
  </pre>

  > Example
  >
  >       curl -X GET https://formhub.org/api/v1/teams/bruize/1

  > Response
  >
  >        {
  >            "url": "https://formhub.org/api/v1/teams/bruize/1",
  >            "name": "Owners",
  >            "organization": "https://formhub.org/api/v1/users/bruize",
  >            "projects": []
  >        }
    """
    queryset = Team.objects.all()
    serializer_class = api_serializers.TeamSerializer
    lookup_fields = ('owner', 'pk')
    lookup_field = 'owner'
    extra_lookup_fields = None

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous():
            user = User.objects.get(pk=-1)
        orgs = user.organizationprofile_set.values('user')
        return Team.objects.filter(organization__in=orgs)

    def get_object(self):
        if 'owner' not in self.kwargs and 'pk' not in self.kwargs:
            raise exceptions.ParseError(
                'Expected URL keyword argument `owner` and `pk`.'
            )
        filter = {
            'organization__username': self.kwargs['owner'],
            'pk': self.kwargs['pk']
        }
        qs = self.filter_queryset(self.get_queryset())
        return get_object_or_404(qs, **filter)

    def list(self, request, **kwargs):
        filter = {}
        if 'owner' in kwargs:
            filter['organization__username'] = kwargs['owner']
        qs = self.filter_queryset(self.get_queryset())
        self.object_list = qs.filter(**filter)
        serializer = self.get_serializer(self.object_list, many=True)
        return Response(serializer.data)


class DataViewSet(viewsets.ViewSet):
    """
This endpoint provides access to submitted data in JSON format. Where:

* `owner` - is organization or user whom the data belongs to
* `formid` - the form unique identifier
* `dataid` - submission data unique identifier

## GET JSON List of data end points
This is a json list of the data end points of `owner` forms
 and/or including public forms and forms shared with `owner`.
<pre class="prettyprint">
  <b>GET</b> /api/v1/data
  <b>GET</b> /api/v1/data/<code>{owner}</code></pre>

  > Example
  >
  >       curl -X GET https://formhub.org/api/v1/data/modilabs

  > Response
  >
  >        {
  >            "dhis2form": "https://formhub.org/api/v1/data/modilabs/4240",
  >            "exp_one": "https://formhub.org/api/v1/data/modilabs/13789",
  >            "userone": "https://formhub.org/api/v1/data/modilabs/10417",
  >        }

## Get Submitted data for a specific form
Provides a list of json submitted data for a specific form.
 <pre class="prettyprint">
  <b>GET</b> /api/v1/data/<code>{owner}</code>/<code>{formid}</code></pre>
  > Example
  >
  >       curl -X GET https://formhub.org/api/v1/data/modilabs/22845

  > Response
  >
  >        [
  >            {
  >                "_id": 4503,
  >                "_bamboo_dataset_id": "",
  >                "_deleted_at": null,
  >                "expense_type": "service",
  >                "_xform_id_string": "exp",
  >                "_geolocation": [
  >                    null,
  >                    null
  >                ],
  >                "end": "2013-01-03T10:26:25.674+03",
  >                "start": "2013-01-03T10:25:17.409+03",
  >                "expense_date": "2011-12-23",
  >                "_status": "submitted_via_web",
  >                "today": "2013-01-03",
  >                "_uuid": "2e599f6fe0de42d3a1417fb7d821c859",
  >                "imei": "351746052013466",
  >                "formhub/uuid": "46ea15e2b8134624a47e2c4b77eef0d4",
  >                "kind": "monthly",
  >                "_submission_time": "2013-01-03T02:27:19",
  >                "required": "yes",
  >                "_attachments": [],
  >                "item": "Rent",
  >                "amount": "35000.0",
  >                "deviceid": "351746052013466",
  >                "subscriberid": "639027...60317"
  >            },
  >            {
  >                ....
  >                "subscriberid": "639027...60317"
  >            }
  >        ]

## Get a single data submission for a given form

Get a single specific submission json data providing `formid`
 and `dataid` as url path parameters, where:

* `owner` - is organization or user whom the data belongs to
* `formid` - is the identifying number for a specific form
* `dataid` - is the unique id of the data, the value of `_id` or `_uuid`

 <pre class="prettyprint">
  <b>GET</b> /api/v1/data/<code>{owner}</code>/<code>{formid}</code>/<code>{dataid}</code></pre>
  > Example
  >
  >       curl -X GET https://formhub.org/api/v1/data/modilabs/22845/4503

  > Response
  >
  >            {
  >                "_id": 4503,
  >                "_bamboo_dataset_id": "",
  >                "_deleted_at": null,
  >                "expense_type": "service",
  >                "_xform_id_string": "exp",
  >                "_geolocation": [
  >                    null,
  >                    null
  >                ],
  >                "end": "2013-01-03T10:26:25.674+03",
  >                "start": "2013-01-03T10:25:17.409+03",
  >                "expense_date": "2011-12-23",
  >                "_status": "submitted_via_web",
  >                "today": "2013-01-03",
  >                "_uuid": "2e599f6fe0de42d3a1417fb7d821c859",
  >                "imei": "351746052013466",
  >                "formhub/uuid": "46ea15e2b8134624a47e2c4b77eef0d4",
  >                "kind": "monthly",
  >                "_submission_time": "2013-01-03T02:27:19",
  >                "required": "yes",
  >                "_attachments": [],
  >                "item": "Rent",
  >                "amount": "35000.0",
  >                "deviceid": "351746052013466",
  >                "subscriberid": "639027...60317"
  >            },
  >            {
  >                ....
  >                "subscriberid": "639027...60317"
  >            }
  >        ]

## Query submitted data of a specific form
Provides a list of json submitted data for a specific form. Use `query`
parameter to apply form data specific, see
<a href="http://www.mongodb.org/display/DOCS/Querying.">
http://www.mongodb.org/display/DOCS/Querying</a>.

For more details see
<a href="https://github.com/modilabs/formhub/wiki/Formhub-Access-Points-(API)#api-parameters">
API Parameters</a>.
 <pre class="prettyprint">
  <b>GET</b> /api/v1/data/<code>{owner}</code>/<code>{formid}</code>?query={"field":"value"}</pre>
  > Example
  >
  >       curl -X GET
  >       https://formhub.org/api/v1/data/modilabs/22845?query={"kind": "monthly"}

  > Response
  >
  >        [
  >            {
  >                "_id": 4503,
  >                "_bamboo_dataset_id": "",
  >                "_deleted_at": null,
  >                "expense_type": "service",
  >                "_xform_id_string": "exp",
  >                "_geolocation": [
  >                    null,
  >                    null
  >                ],
  >                "end": "2013-01-03T10:26:25.674+03",
  >                "start": "2013-01-03T10:25:17.409+03",
  >                "expense_date": "2011-12-23",
  >                "_status": "submitted_via_web",
  >                "today": "2013-01-03",
  >                "_uuid": "2e599f6fe0de42d3a1417fb7d821c859",
  >                "imei": "351746052013466",
  >                "formhub/uuid": "46ea15e2b8134624a47e2c4b77eef0d4",
  >                "kind": "monthly",
  >                "_submission_time": "2013-01-03T02:27:19",
  >                "required": "yes",
  >                "_attachments": [],
  >                "item": "Rent",
  >                "amount": "35000.0",
  >                "deviceid": "351746052013466",
  >                "subscriberid": "639027...60317"
  >            },
  >            {
  >                ....
  >                "subscriberid": "639027...60317"
  >            }
  >        ]

## Query submitted data of a specific form using Tags
Provides a list of json submitted data for a specific form matching specific
tags. Use the `tags` query parameter to filter the list of forms, `tags`
should be a comma separated list of tags.

 <pre class="prettyprint">
  <b>GET</b> /api/v1/data?<code>tags</code>=<code>tag1,tag2</code></pre>
 <pre class="prettyprint">
  <b>GET</b> /api/v1/data/<code>{owner}</code>?<code>tags</code>=<code>tag1,tag2</code></pre>
 <pre class="prettyprint">
  <b>GET</b> /api/v1/data/<code>{owner}</code>/<code>{formid}</code>?<code>tags</code>=<code>tag1,tag2</code></pre>

  > Example
  >
  >       curl -X GET https://formhub.org/api/v1/data/modilabs/22845?tags=monthly

## Tag a submission data point

A `POST` payload of parameter `tags` with a comma separated list of tags.

Examples

- `animal fruit denim` - space delimited, no commas
- `animal, fruit denim` - comma delimited

 <pre class="prettyprint">
  <b>POST</b> /api/v1/data/<code>{owner}</code>/<code>{formid}</code>/<code>{dataid}</code>/labels</pre>

Payload

    {"tags": "tag1, tag2"}

## Delete a specific tag from a submission

 <pre class="prettyprint">
  <b>DELETE</b> /api/v1/data/<code>{owner}</code>/<code>{formid}</code>/<code>{dataid}</code>/labels/<code>tag_name</code></pre>

  > Request
  >
  >       curl -X DELETE https://formhub.org/api/v1/data/modilabs/28058/20/labels/tag1
  or to delete the tag "hello world"
  >
  >       curl -X DELETE https://formhub.org/api/v1/data/modilabs/28058/20/labels/hello%20world
  >
  > Response
  >
  >        HTTP 200 OK
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, ]
    lookup_field = 'owner'
    lookup_fields = ('owner', 'formid', 'dataid')
    extra_lookup_fields = None

    queryset = Instance.objects.all()

    def _get_accessible_forms(self, owner=None):
        xforms = []
        # list public forms incase anonymous user
        if self.request.user.is_anonymous():
            xforms = XForm.public_forms().order_by('?')[:10]
            # select only  the random 10, allows chaining later on
            xforms = XForm.objects.filter(pk__in=[x.pk for x in xforms])
        else:
            xforms = XForm.objects.filter(user__username=owner)
        return xforms.distinct()

    def _get_formlist_data_points(self, request, owner=None):
        xforms = self._get_accessible_forms(owner)
        # filter by tags if available.
        tags = self.request.QUERY_PARAMS.get('tags', None)
        if tags and isinstance(tags, basestring):
            tags = tags.split(',')
            xforms = xforms.filter(tags__name__in=tags).distinct()
        rs = {}
        for xform in xforms.distinct():
            point = {u"%s" % xform.id_string:
                     reverse("data-list", kwargs={
                             "formid": xform.pk,
                             "owner": xform.user.username},
                             request=request)}
            rs.update(point)
        return rs

    def _get_form_data(self, xform, **kwargs):
        query = kwargs.get('query', {})
        query = query if query is not None else {}
        if xform:
            query[ParsedInstance.USERFORM_ID] =\
                u'%s_%s' % (xform.user.username, xform.id_string)
        query = json.dumps(query) if isinstance(query, dict) else query
        margs = {
            'query': query,
            'fields': kwargs.get('fields', None),
            'sort': kwargs.get('sort', None)
        }
        cursor = ParsedInstance.query_mongo_minimal(**margs)
        records = list(record for record in cursor)
        return records

    def list(self, request, owner=None, formid=None, dataid=None, **kwargs):
        data = None
        xform = None
        query = None
        tags = self.request.QUERY_PARAMS.get('tags', None)
        if owner is None and not request.user.is_anonymous():
            owner = request.user.username
        if not formid and not dataid and not tags:
            data = self._get_formlist_data_points(request, owner)
        if formid:
            xform = check_and_set_form_by_id(int(formid), request)
            if not xform:
                raise exceptions.PermissionDenied(
                    _("You do not have permission to "
                      "view data from this form."))
        if xform and dataid and dataid == 'labels':
            return Response(list(xform.tags.names()))
        if xform and dataid:
            query = {'_id': int(dataid)}
        rquery = request.QUERY_PARAMS.get('query', None)
        if rquery:
            rquery = json.loads(rquery)
            if query:
                rquery.update(json.loads(query))
        if tags:
            query = query if query else {}
            query['_tags'] = {'$all': tags.split(',')}
        if xform:
            data = self._get_form_data(xform, query=query)
        if not xform and not data:
            xforms = self._get_accessible_forms(owner)
            query[ParsedInstance.USERFORM_ID] = {
                '$in': [
                    u'%s_%s' % (form.user.username, form.id_string)
                    for form in xforms]
            }
            # query['_id'] = {'$in': [form.pk for form in xforms]}
            data = self._get_form_data(xform, query=query)
        if dataid and len(data):
            data = data[0]
        return Response(data)

    @action(methods=['GET', 'POST', 'DELETE'], extra_lookup_fields=['label', ])
    def labels(self, request, owner, formid, dataid, **kwargs):
        class TagForm(forms.Form):
            tags = TagField()
        if owner is None and not request.user.is_anonymous():
            owner = request.user.username
        xform = check_and_set_form_by_id(int(formid), request)
        if not xform:
            raise exceptions.PermissionDenied(
                _("You do not have permission to "
                    "view data from this form."))
        status = 400
        instance = get_object_or_404(ParsedInstance, instance__pk=int(dataid))
        if request.method == 'POST':
            form = TagForm(request.DATA)
            if form.is_valid():
                tags = form.cleaned_data.get('tags', None)
                if tags:
                    for tag in tags:
                        instance.instance.tags.add(tag)
                    instance.save()
                    status = 201
        label = kwargs.get('label', None)
        if request.method == 'GET' and label:
            data = [
                i['name'] for i in
                instance.instance.tags.filter(name=label).values('name')]
        elif request.method == 'DELETE' and label:
            count = instance.instance.tags.count()
            instance.instance.tags.remove(label)
            # Accepted, label does not exist hence nothing removed
            if count == instance.instance.tags.count():
                status = 202
            data = list(instance.instance.tags.names())
        else:
            data = list(instance.instance.tags.names())
        if request.method == 'GET':
            status = 200
        return Response(data, status=status)
