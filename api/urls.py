from django.conf.urls import url
from rest_framework import routers
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.urlpatterns import format_suffix_patterns
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
        base_regex = '(?P<{lookup_field}>[^/]+)'
        lookup_fields = getattr(viewset, 'lookup_fields', None)
        if lookup_fields:
            for lookup_field in lookup_fields:
                ret.append(base_regex.format(lookup_field=lookup_field))
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

        class FormhubApi(api_views.APIView):
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
            lookups = self.get_lookup_regexes(viewset)
            if lookups:
                # lookup = lookups[0]
                lookups = u'/'.join(lookups)
            else:
                lookups = u''
            routes = self.get_routes(viewset)
            for route in routes:
                mapping = self.get_method_map(viewset, route.mapping)
                if not mapping:
                    continue
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
router.register(r'data', api_views.DataList, base_name='data')
router.urls.append(
    url(r'^data$', api_views.DataList.as_view(), name='data-list'))
router.urls.append(
    url(r'^data/(?P<formid>[^/]+)$',
        api_views.DataList.as_view(), name='data-list'))
router.urls.append(
    url(r'^data/(?P<formid>[^/]+)/(?P<dataid>[^/]+)$',
        api_views.DataList.as_view(), name='data-detail'))
