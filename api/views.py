from django.contrib.auth.models import User

from rest_framework import viewsets
from api import serializers as api_serializers
from api import mixins

from main.models import UserProfile

from odk_logger.models import XForm

from api.models import Project


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = api_serializers.UserSerializer
    lookup_field = 'username'


class UserProfileViewSet(mixins.ObjectLookupMixin, viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = api_serializers.UserProfileSerializer
    lookup_field = 'user'


class XFormViewSet(viewsets.ModelViewSet):
    queryset = XForm.objects.all()
    serializer_class = api_serializers.XFormSerializer


class ProjectViewSet(mixins.MultiLookupMixin, viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = api_serializers.ProjectSerializer
    lookup_fields = ('owner', 'pk')
    lookup_field = 'owner'
