from django.conf.urls import url
from rest_framework import routers
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.views import APIView

from api import views as api_views


class MultiLookupRouter(routers.DefaultRouter):
    def __init__(self, *args, **kwargs):
        super(MultiLookupRouter, self).__init__(*args, **kwargs)
        self.lookups_routes = []
        self.lookups_routes.append(routers.Route(
            url=r'^{prefix}/{lookups}{trailing_slash}$',
            mapping={
                'get': 'retrieve',
                'put': 'update',
                'patch': 'partial_update',
                'delete': 'destroy'
            },
            name='{basename}-detail',
            initkwargs={'suffix': 'Instance'}
        )
        )
        self.lookups_routes.append(routers.Route(
            url=r'^{prefix}/{lookup}{trailing_slash}$',
            mapping={
                'get': 'list',
                'post': 'create'
            },
            name='{basename}-list',
            initkwargs={'suffix': 'List'}
        ))
        self.lookups_routes.append(routers.Route(
            url=r'^{prefix}/{lookups}{trailing_slash}$',
            mapping={
                'get': 'list',
                'post': 'create'
            },
            name='{basename}-list',
            initkwargs={'suffix': 'List'}
        ))
        # Dynamically generated routes.
        # Generated using @action or @link decorators on methods of the viewset
        self.lookups_routes.append(routers.Route(
            url=[
                r'^{prefix}/{lookups}/{methodname}{trailing_slash}$',
                r'^{prefix}/{lookups}/{methodname}/{extra}{trailing_slash}$'],
            mapping={
                '{httpmethod}': '{methodname}',
            },
            name='{basename}-{methodnamehyphen}',
            initkwargs={}
        ))

    def get_extra_lookup_regexes(self, route):
        ret = []
        base_regex = '(?P<{lookup_field}>[^/]+)'
        if 'extra_lookup_fields' in route.initkwargs:
            for lookup_field in route.initkwargs['extra_lookup_fields']:
                ret.append(base_regex.format(lookup_field=lookup_field))
        return '/'.join(ret)

    def get_lookup_regexes(self, viewset):
        ret = []
        lookup_fields = getattr(viewset, 'lookup_fields', None)
        if lookup_fields:
            for i in range(1, len(lookup_fields)):
                tmp = []
                for lookup_field in lookup_fields[:i + 1]:
                    if lookup_field == lookup_fields[i]:
                        base_regex = '(?P<{lookup_field}>[^/.]+)'
                    else:
                        base_regex = '(?P<{lookup_field}>[^/]+)'
                    tmp.append(base_regex.format(lookup_field=lookup_field))
                ret.append(tmp)
        return ret

    def get_lookup_routes(self, viewset):
        ret = [self.routes[0]]
        # Determine any `@action` or `@link` decorated methods on the viewset
        dynamic_routes = []
        for methodname in dir(viewset):
            attr = getattr(viewset, methodname)
            httpmethods = getattr(attr, 'bind_to_methods', None)
            if httpmethods:
                httpmethods = [method.lower() for method in httpmethods]
                dynamic_routes.append((httpmethods, methodname))

        for route in self.lookups_routes:
            if route.mapping == {'{httpmethod}': '{methodname}'}:
                # Dynamic routes (@link or @action decorator)
                for httpmethods, methodname in dynamic_routes:
                    initkwargs = route.initkwargs.copy()
                    initkwargs.update(getattr(viewset, methodname).kwargs)
                    mapping = dict(
                        (httpmethod, methodname) for httpmethod in httpmethods)
                    name = routers.replace_methodname(route.name, methodname)
                    if 'extra_lookup_fields' in initkwargs:
                        uri = route.url[1]
                        uri = routers.replace_methodname(uri, methodname)
                        ret.append(routers.Route(
                            url=uri, mapping=mapping, name='%s-extra' % name,
                            initkwargs=initkwargs,
                        ))
                    uri = routers.replace_methodname(route.url[0], methodname)
                    ret.append(routers.Route(
                        url=uri, mapping=mapping, name=name,
                        initkwargs=initkwargs,
                    ))
            else:
                # Standard route
                ret.append(route)
        return ret

    def get_routes(self, viewset):
        ret = []
        lookup_fields = getattr(viewset, 'lookup_fields', None)
        if lookup_fields:
            ret = self.get_lookup_routes(viewset)
        else:
            ret = super(MultiLookupRouter, self).get_routes(viewset)
        return ret

    def get_api_root_view(self):
        """
        Return a view to use as the API root.
        """
        api_root_dict = {}
        list_name = self.routes[0].name
        for prefix, viewset, basename in self.registry:
            api_root_dict[prefix] = list_name.format(basename=basename)

        class FormhubApi(APIView):
            """
            ## JSON Rest API

            Formhub provides the following JSON api endpoints:

            * [/api/v1/users](/api/v1/users) - List, Retrieve username, first
            and last name
            * [/api/v1/profiles](/api/v1/profiles) - List, Create,
            Update, user information
            * [/api/v1/orgs](/api/v1/orgs) - List, Retrieve, Create,
            Update organization and organization info
            * [/api/v1/projects](/api/v1/projects) - List, Retrieve, Create,
             Update organization projects, forms
            * [/api/v1/teams](/api/v1/teams) - List, Retrieve, Create,
            Update teams
            * [/api/v1/forms](/api/v1/forms) - List, Retrieve
            xlsforms information
            * [/api/v1/data](/api/v1/data) - List, Retrieve submission data

            ## Status Codes

            * **200** - Successful [`GET`, `PATCH`, `PUT`]
            * **201** - Resource successfully created [`POST`]
            * **204** - Resouce successfully deleted [`DELETE`]
            * **403** - Permission denied to resource
            * **404** - Resource was not found

            ## Authentication

            Formhub JSON API enpoints support both Basic authentication
            and API Token Authentication through the `Authorization` header.

            ### Basic Authentication

            Example using curl:

                curl -X GET https://formhub.org/api/v1 -u username:password

            ### Token Authentication

            Example using curl:

                curl -X GET https://formhub.org/api/v1 -H "Authorization: Token TOKEN_KEY"

            ### Formhub Tagging API

            * [Filter form list by
            * tags.](/api/v1/forms#get-list-of-forms-with-specific-tags)
            * [List Tags for a specific form.](/api/v1/forms#get-list-of-tags-for-a-specific-form)
            * [Tag Forms.](/api/v1/forms#tag-forms)
            * [Delete a specific tag.](/api/v1/forms#delete-a-specific-tag)
            * [List form data by tag.](/api/v1/data#query-submitted-data-of-a-specific-form-using-tags)
            * [Tag a specific submission](/api/v1/data#tag-a-submission-data-point)

            ## Using Oauth2 with formhub API

            You can learn more about oauth2 from [http://tools.ietf.org/html/rfc6749](http://tools.ietf.org/html/rfc6749).

            ### 1. Register your client application with formhub - [register](/o/applications/register/)

            - `name` - name of your application
            - `client_type` - Client Type: select confidential
            - `authorization_grant_type` - Authorization grant type: Authorization code
            - `redirect_uri` - Redirect urls: redirection endpoint

            Keep note of the `client_id` and the `client_secret`, it is required when
             requesting for an `access_token`.

            ### 2. Authorize client application.

            The authorization url is of the form:

               `GET`  /o/authorize?client_id=XXXXXX&response_type=code&state=abc

            example:

                http://localhost:8000/o/authorize?client_id=e8x4zzJJIyOikDqjPcsCJrmnU22QbpfHQo4HhRnv&response_type=code&state=xyz

            Note: Providing the url to any user will prompt for a password and
            request for read and write permission for the application whose `client_id` is specified.

            Where:

            - `client_id` - is the client application id - ensure its urlencoded
            - `response_type` - should be code
            - `state` - a random state string that you client application will get when redirection happens

            What happens:

            1. a login page is presented, the username used to login determines the account that provides access.
            2. redirection to the client application occurs, the url is of the form:

                REDIRECT_URI/?state=abc&code=YYYYYYYYY

            example redirect uri

                http://localhost:30000/?state=xyz&code=SWWk2PN6NdCwfpqiDiPRcLmvkw2uWd

            - `code` - is the code to use to request for `access_token`
            - `state` - same state string used during authorization request

            Your client application should use the `code` to request for an access_token.

            ### 3. Request for access token.

            Request:

                `POST` /o/token

            Payload:

                grant_type=authorization_code&code=YYYYYYYYY&client_id=XXXXXX&redirect_uri=http://redirect/uri/path

            curl example:

                curl -X POST -d "grant_type=authorization_code&code=PSwrMilnJESZVFfFsyEmEukNv0sGZ8&client_id=e8x4zzJJIyOikDqjPcsCJrmnU22QbpfHQo4HhRnv&redirect_uri=http://localhost:30000" "http://localhost:8000/o/token/" --user "e8x4zzJJIyOikDqjPcsCJrmnU22QbpfHQo4HhRnv:xo7i4LNpMjH2lqHQQnBrLOVh7dZkK8qffn68dwtwd4iAq6uSwKA8d5u2YSqD3N7AFivV3cGAkJyQiAneu6BgCdG9YjEdYi0eA0O9KhLtjtPIYOjVCTGeCgbfNQaeuxe1"

            Response:

                {
                    "access_token": "Q6dJBs9Vkf7a2lVI7NKLT8F7c6DfLD",
                    "token_type": "Bearer", "expires_in": 36000,
                    "refresh_token": "53yF3uz79K1fif2TPtNBUFJSFhgnpE",
                    "scope": "read write groups"
                }

            Where:

            - `access_token` - access token - expires
            - `refresh_token` - token to use to request a new `access_token` in case it has expored.

            Now that you have an `access_token` you can make API calls.

            ### 4. Accessing the Formhub API using the `access_token`.

            Example using curl:

                curl -X GET https://formhub.org/api/v1 -H "Authorization: Bearer ACCESS_TOKEN"
            """
            _ignore_model_permissions = True

            def get(self, request, format=None):
                ret = {}
                for key, url_name in api_root_dict.items():
                    ret[key] = reverse(
                        url_name, request=request, format=format)
                return Response(ret)

        return FormhubApi.as_view()

    def get_urls(self):
        ret = []

        if self.include_root_view:
            root_url = url(r'^$', self.get_api_root_view(),
                           name=self.root_view_name)
            ret.append(root_url)
        for prefix, viewset, basename in self.registry:
            lookup = self.get_lookup_regex(viewset)
            lookup_list = self.get_lookup_regexes(viewset)
            if lookup_list:
                # lookup = lookups[0]
                lookup_list = [u'/'.join(k) for k in lookup_list]
            else:
                lookup_list = [u'']
            routes = self.get_routes(viewset)
            for route in routes:
                mapping = self.get_method_map(viewset, route.mapping)
                if not mapping:
                    continue
                for lookups in lookup_list:
                    regex = route.url.format(
                        prefix=prefix,
                        lookup=lookup,
                        lookups=lookups,
                        trailing_slash=self.trailing_slash,
                        extra=self.get_extra_lookup_regexes(route)
                    )
                    view = viewset.as_view(mapping, **route.initkwargs)
                    name = route.name.format(basename=basename)
                    ret.append(url(regex, view, name=name))
        if self.include_format_suffixes:
            ret = format_suffix_patterns(ret)
        return ret

router = MultiLookupRouter(trailing_slash=False)
router.register(r'users', api_views.UserViewSet)
router.register(r'profiles', api_views.UserProfileViewSet)
router.register(r'orgs', api_views.OrgProfileViewSet)
router.register(r'forms', api_views.XFormViewSet)
router.register(r'projects', api_views.ProjectViewSet)
router.register(r'teams', api_views.TeamViewSet)
router.register(r'data', api_views.DataViewSet, base_name='data')
