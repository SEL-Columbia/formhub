from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action

from api import serializers as api_serializers
from api import mixins
from api import utils

from main.models import UserProfile

from odk_logger.models import XForm

from api.models import Project, OrganizationProfile, ProjectXForm


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


class ProjectViewSet(mixins.MultiLookupMixin, viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = api_serializers.ProjectSerializer
    lookup_fields = ('owner', 'pk')
    lookup_field = 'owner'

    def list(self, request, **kwargs):
        filter = {}
        if 'owner' in kwargs:
            filter['organization__username'] = kwargs['owner']
        qs = self.filter_queryset(self.get_queryset())
        self.object_list = qs.filter(**filter)
        serializer = self.get_serializer(self.object_list, many=True)
        return Response(serializer.data)

    @action(methods=['POST', 'GET'])
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
        qs = ProjectXForm.objects.filter(**filter)
        data = [px.xform for px in qs]
        serializer = api_serializers.XFormSerializer(data, many=True)
        return Response(serializer.data)
