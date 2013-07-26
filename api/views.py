import json

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _

from rest_framework import viewsets
from rest_framework import exceptions
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.decorators import action
from rest_framework.settings import api_settings
from rest_framework.renderers import BaseRenderer

from api import serializers as api_serializers
from api import mixins
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
        return User.objects.filter(pk__in=user.userprofile_set.values('user'))


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
        return user.userprofile_set.all()


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
>           "url": "http://localhost/api/v1/forms/modilabs/28058",
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
>           "owner": "http://localhost/api/v1/users/modilabs",
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
>           "url": "http://localhost/api/v1/forms/modilabs/28058",
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
  >       curl -X GET https://formhub.org/api/v1/forms/28058/form.json

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
    """
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES + [SurveyRenderer]
    queryset = XForm.objects.all()
    serializer_class = api_serializers.XFormSerializer
    lookup_fields = ('owner', 'pk')
    lookup_field = 'owner'

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous():
            user = User.objects.get(pk=-1)
        user_forms = user.xforms.values('pk')
        project_forms = user.projectxform_set.values('xform')
        return XForm.objects.filter(
            Q(pk__in=user_forms) | Q(pk__in=project_forms))

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
>           "url": "http://localhost/api/v1/projects/modilabs/1",
>           "owner": "http://localhost/api/v1/users/modilabs",
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
>               "url": "http://localhost/api/v1/projects/modilabs/1",
>               "owner": "http://localhost/api/v1/users/modilabs",
>               "name": "project 1",
>               "date_created": "2013-07-24T13:37:39Z",
>               "date_modified": "2013-07-24T13:37:39Z"
>           },
>           {
>               "url": "http://localhost/api/v1/projects/modilabs/4",
>               "owner": "http://localhost/api/v1/users/modilabs",
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
>           "url": "http://localhost/api/v1/projects/modilabs/1",
>           "owner": "http://localhost/api/v1/users/modilabs",
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
>           "url": "http://localhost/api/v1/forms/28058",
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
>           "url": "http://localhost/api/v1/forms/28058",
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
                serializer = api_serializers.XFormSerializer(
                    survey, context={'request': request})
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
  >                "url": "http://localhost/api/v1/teams/bruize/1",
  >                "name": "Owners",
  >                "organization": "http://localhost/api/v1/users/bruize",
  >                "projects": []
  >            },
  >            {
  >                "url": "http://localhost/api/v1/teams/bruize/2",
  >                "name": "demo team",
  >                "organization": "http://localhost/api/v1/users/bruize",
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
  >            "url": "http://localhost/api/v1/teams/bruize/1",
  >            "name": "Owners",
  >            "organization": "http://localhost/api/v1/users/bruize",
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


class DataList(APIView):
    """
This endpoint provides access to submitted data in JSON format.

## GET JSON List of data end points
This is a json list of the data end points of your forms
 and/or including public forms and forms shared with you.
<pre class="prettyprint">
  <b>GET</b> /api/v1/data</pre>

  > Example
  >
  >       curl -X GET https://formhub.org/api/v1/data

  > Response
  >
  >        {
  >            "dhis2form": "http://localhost/api/v1/data/4240",
  >            "exp_one": "http://localhost/api/v1/data/13789",
  >            "userone": "http://localhost/api/v1/data/10417",
  >        }

## Get Submitted data for a specific form
Provides a list of json submitted data for a specific form,
 where `formid` is the identifying number for a specific form.
 <pre class="prettyprint">
  <b>GET</b> /api/v1/data/<code>{formid}</code></pre>
  > Example
  >
  >       curl -X GET https://formhub.org/api/v1/data/22845

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

* `formid` is the identifying number for a specific form
* `dataid` is the unique id of the data, the value of `_id` or `_uuid`

 <pre class="prettyprint">
  <b>GET</b> /api/v1/data/<code>{formid}</code>/<code>{dataid}</code></pre>
  > Example
  >
  >       curl -X GET https://formhub.org/api/v1/data/22845/4503

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
    """
    queryset = Instance.objects.all()

    def _get_formlist_data_points(self, request):
        xforms = []
        # list public points incase anonymous user
        if request.user.is_anonymous():
            xforms = XForm.public_forms().order_by('?')[:10]
        else:
            # list data points authenticated user has access to
            xforms = XForm.objects.filter(user=request.user)
        rs = {}
        for xform in xforms:
            point = {u"%s" % xform.id_string:
                     reverse("data-list", kwargs={"formid": xform.pk},
                             request=request)}
            rs.update(point)
        return rs

    def _get_form_data(self, xform, **kwargs):
        margs = {
            'username': xform.user.username,
            'id_string': xform.id_string,
            'query': kwargs.get('query', None),
            'fields': kwargs.get('fields', None),
            'sort': kwargs.get('sort', None)
        }
        cursor = ParsedInstance.query_mongo(**margs)
        records = list(record for record in cursor)
        return records

    def get(self, request, formid=None, dataid=None, **kwargs):
        """
        Display submission data.
        If no parameter is given, it displays a dictionary of public data urls.

        formid - primary key for the form
        dataid - primary key for the data submission
        """
        data = None
        xform = None
        query = None
        if not formid and not dataid:
            data = self._get_formlist_data_points(request)
        if formid:
            xform = check_and_set_form_by_id(int(formid), request)
            if not xform:
                raise exceptions.PermissionDenied(
                    _("You do not have permission to "
                      "view data from this form."))
        if xform and dataid:
            query = json.dumps({'_id': int(dataid)})
        if xform:
            data = self._get_form_data(xform, query=query)
        if dataid and len(data):
            data = data[0]
        return Response(data)
