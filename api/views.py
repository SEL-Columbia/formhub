from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action

from api import serializers as api_serializers
from api import mixins
from api import tools as utils

from main.models import UserProfile

from odk_logger.models import XForm

from api.models import Project, OrganizationProfile, ProjectXForm, Team


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = api_serializers.UserSerializer
    lookup_field = 'username'


class UserProfileViewSet(mixins.ObjectLookupMixin, viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = api_serializers.UserProfileSerializer
    lookup_field = 'user'


class OrgProfileViewSet(mixins.ObjectLookupMixin, viewsets.ModelViewSet):
    queryset = OrganizationProfile.objects.all()
    serializer_class = api_serializers.OrganizationSerializer
    lookup_field = 'user'


class XFormViewSet(viewsets.ModelViewSet):
    queryset = XForm.objects.all()
    serializer_class = api_serializers.XFormSerializer


def extra_kwargs(**kwargs):
    def decorator(func):
        func.extra_kwargs = kwargs
        return func
    return decorator


class ProjectViewSet(mixins.MultiLookupMixin, viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = api_serializers.ProjectSerializer
    lookup_fields = ('owner', 'pk')
    lookup_field = 'owner'
    extra_lookup_fields = None

    def list(self, request, **kwargs):
        filter = {}
        if 'owner' in kwargs:
            filter['organization__username'] = kwargs['owner']
        qs = self.filter_queryset(self.get_queryset())
        self.object_list = qs.filter(**filter)
        serializer = self.get_serializer(self.object_list, many=True)
        return Response(serializer.data)

    @action(methods=['POST', 'GET'], extra_lookup_fields=['formid', ])
    def forms(self, request, **kwargs):
        project = get_object_or_404(
            Project, pk=kwargs.get('pk', None),
            organization__username=kwargs.get('owner', None))
        if request.method.upper() == 'POST':
            survey = utils.publish_project_xform(request, project)
            if isinstance(survey, XForm):
                serializer = api_serializers.XFormSerializer(survey)
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
        serializer = api_serializers.XFormSerializer(data, many=many)
        return Response(serializer.data)


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = api_serializers.TeamSerializer
    lookup_fields = ('owner', 'pk')
    lookup_field = 'owner'
    extra_lookup_fields = None

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
