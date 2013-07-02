from django.conf.urls.defaults import url
from rest_framework import routers
from api import views as api_views


class MultiLookupRouter(routers.DefaultRouter):
    def __init__(self, *args, **kwargs):
        super(MultiLookupRouter, self).__init__(*args, **kwargs)
        self.routes = []
        # List route.
        self.routes.append(routers.Route(
            url=r'^{prefix}$',
            mapping={
                'get': 'list',
                'post': 'create'
            },
            name='{basename}-list',
            initkwargs={'suffix': 'List'}
        ))
        # Detail route.
        self.routes.append(routers.Route(
            url=r'^{prefix}/{lookup}$',
            mapping={
                'get': 'retrieve',
                'put': 'update',
                'patch': 'partial_update',
                'delete': 'destroy'
            },
            name='{basename}-detail',
            initkwargs={'suffix': 'Instance'}
        ))
        self.lookups_routes = []
        self.lookups_routes.append(routers.Route(
            url=r'^{prefix}/{lookups}$',
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
            url=r'^{prefix}/{lookup}$',
            mapping={
                'get': 'list',
                'post': 'create'
            },
            name='{basename}-list',
            initkwargs={'suffix': 'List'}
        ))

    def get_lookup_regexes(self, viewset):
        ret = []
        base_regex = '(?P<{lookup_field}>[^/]+)'
        lookup_fields = getattr(viewset, 'lookup_fields', None)
        if lookup_fields:
            for lookup_field in lookup_fields:
                ret.append(base_regex.format(lookup_field=lookup_field))
        return ret

    def get_routes(self, viewset):
        ret = []
        lookup_fields = getattr(viewset, 'lookup_fields', None)
        if lookup_fields:
            ret.append(self.routes[0])
            ret.extend(self.lookups_routes)
        else:
            ret = super(MultiLookupRouter, self).get_routes(viewset)
        return ret

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
                    lookups=lookups
                )
                view = viewset.as_view(mapping, **route.initkwargs)
                name = route.name.format(basename=basename)
                ret.append(url(regex, view, name=name))
        return ret

router = MultiLookupRouter()
router.register(r'users', api_views.UserProfileViewSet)
router.register(r'orgs', api_views.OrgProfileViewSet)
router.register(r'u', api_views.UserViewSet)
router.register(r'forms', api_views.XFormViewSet)
router.register(r'projects', api_views.ProjectViewSet)
